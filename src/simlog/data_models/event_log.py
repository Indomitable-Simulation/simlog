import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class LoggedEvent(BaseModel):
    """
    Class for logging events in the simulation.
    """

    topic: str = Field(..., description="Event topic")
    parent: str | None = Field(None, description="Parent event ID")
    single_reference: str | None = Field(None, description="Single reference ID")
    sim_time: float = Field(..., description="Simulation time in seconds")
    value: Any = Field(None, description="Event value")
    simpy_id: int = Field(..., description="ID assigned to the event by the SimPy engine")
    simpy_priority: int = Field(..., description="Priority assigned to the event by the SimPy engine")
    component_state: str | None = Field(None, description="Component state")


class Loggable:
    def get_loggable_data(self):
        """Return a dictionary of data that should be logged."""
        raise NotImplementedError


class EventLog(BaseModel):
    logs: list[LoggedEvent]

    def json_dump(self, path: Path, event_topic: Enum):
        event_descriptions = {member.value.value: member.value.description for member in event_topic}
        dump_dict = {
            "event_descriptions": event_descriptions,
            "logs": [self.convert_log_to_dict(log) for log in self.logs],
        }
        with open(path, "w") as f:
            json.dump(dump_dict, f, indent=4)

    def convert_log_to_dict(self, log):
        log_dict = log.dict()
        if isinstance(log.value, Loggable):
            log_dict["value"] = log.value.get_loggable_data()
        return log_dict
