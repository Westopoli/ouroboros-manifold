class TriggerBus:
    def __init__(self):
        self.flags: dict[str, bool] = {}
        self.values: dict[str, float | str] = {}

    def set_flag(self, name: str) -> None:
        self.flags[name] = True

    def clear_flag(self, name: str) -> None:
        self.flags[name] = False

    def get_flag(self, name: str) -> bool:
        return self.flags.get(name, False)

    def set_value(self, name: str, value: float | str) -> None:
        self.values[name] = value

    def get_value(self, name: str) -> float | str | None:
        return self.values.get(name)

    def to_dict(self) -> dict:
        return {"flags": dict(self.flags), "values": dict(self.values)}

    @classmethod
    def from_dict(cls, data: dict) -> "TriggerBus":
        bus = cls()
        bus.flags = dict(data.get("flags", {}))
        bus.values = dict(data.get("values", {}))
        return bus
