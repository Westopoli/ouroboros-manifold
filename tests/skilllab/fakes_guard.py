"""TimelineFakeEngine plus order_guard (om_command_guard); the order log gets kind "guard" with goal None."""
from fakes_timeline import TimelineFakeEngine


class GuardFakeEngine(TimelineFakeEngine):
    def order_guard(self, w, unit_ids):
        self.calls.append(("order_guard", w, list(unit_ids)))
        self.order_log.append((self.step_count, "guard", list(unit_ids), None))
