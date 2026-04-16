import asyncio
import json
import logging
import os as _os
import signal

import config
import command_ingest
from snapshot_serializer import full_snapshot, delta, DeadReckoningTracker

logger = logging.getLogger(__name__)


class SocketServer:
    def __init__(self, host=None, port=None, engine_factory=None):
        self.host = host or config.SOCKET_HOST
        self.port = port or config.SOCKET_PORT
        self.engine_factory = engine_factory  # callable() → TacticalEngine, or None for hello-only
        self._server = None

    async def _handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        logger.info("client connected: %s", addr)

        if self.engine_factory is None:
            try:
                writer.write((json.dumps({"type": "hello"}) + "\n").encode())
                await writer.drain()
                logger.info("sent hello to %s", addr)
            except Exception as exc:
                logger.warning("error sending hello to %s: %s", addr, exc)
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
                logger.info("client disconnected: %s (hello-only mode)", addr)
            return

        engine = self.engine_factory()
        dr_tracker = DeadReckoningTracker()
        prev = full_snapshot(engine)

        async def _read_commands():
            try:
                while True:
                    line = await reader.readline()
                    if not line:
                        break
                    try:
                        pkt = json.loads(line.decode())
                    except json.JSONDecodeError:
                        continue
                    command_ingest.ingest(pkt, engine)
            except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
                pass

        read_task = asyncio.create_task(_read_commands())

        try:
            writer.write((json.dumps(prev) + "\n").encode())
            await writer.drain()

            tick_interval = 1.0 / config.TICK_HZ
            loop = asyncio.get_event_loop()
            start_time = loop.time()
            next_snap_at = start_time + config.SNAPSHOT_INTERVAL_SEC
            tick_num = 0

            while True:
                engine.step()

                now = loop.time()
                if now >= next_snap_at:
                    pkt = full_snapshot(engine)
                    dr_tracker.reset()  # client has fresh ground truth
                    next_snap_at += config.SNAPSHOT_INTERVAL_SEC
                else:
                    pkt = delta(engine, prev, dr_tracker)

                prev = full_snapshot(engine)  # keep prev current for next delta

                writer.write((json.dumps(pkt) + "\n").encode())
                await writer.drain()

                tick_num += 1
                sleep_for = (start_time + tick_num * tick_interval) - loop.time()
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)

        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass
        except Exception as exc:
            logger.warning("tick loop error for %s: %s", addr, exc)
        finally:
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            logger.info("client disconnected: %s", addr)

    async def start(self):
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        addr = self._server.sockets[0].getsockname()
        logger.info("socket server listening on %s:%s", addr[0], addr[1])
        async with self._server:
            try:
                await self._server.serve_forever()
            except asyncio.CancelledError:
                pass  # clean shutdown via stop()

    def stop(self):
        if self._server:
            self._server.close()
            logger.info("socket server stopped")


def run(host=None, port=None, engine_factory=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    server = SocketServer(host, port, engine_factory)

    loop = asyncio.new_event_loop()

    def _shutdown(signum, frame):
        logger.info("shutdown signal received")
        server.stop()
        _os._exit(0)  # force-kill; wait_closed() deadlocks with active connections

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        loop.run_until_complete(server.start())
    finally:
        loop.close()


if __name__ == "__main__":
    run()
