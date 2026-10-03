"""TimelineFakeEngine plus order_group_move (om_command_group_move): logs ("order_group_move", w, ids, x, y) in calls
and (tick, "group_move", ids, (x, y)) in order_log. Returns 1 (a group id), like the library for a grouped order."""
from fakes_timeline import TimelineFakeEngine


class GroupMoveFakeEngine(TimelineFakeEngine):
    def order_group_move(self, w, unit_ids, x, y):
        self.calls.append(("order_group_move", w, list(unit_ids), x, y))
        self.order_log.append((self.step_count, "group_move", list(unit_ids), (x, y)))
        return 1
