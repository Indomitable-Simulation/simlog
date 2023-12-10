from enum import Enum

from simlog.events.events import EventTopicValue


class EventTopic(Enum):
    """List of possible events."""

    PATIENT_JOINED_QUEUE = EventTopicValue(value="PATIENT_JOINED_QUEUE", description="Patient joined the queue")
    PATIENT_ARRIVED_AT_DESK = EventTopicValue(
        value="PATIENT_ARRIVED_AT_DESK", description="Patient being served by reception staff"
    )
    PATIENT_DONE_BEING_SERVED = EventTopicValue(
        value="PATIENT_DONE_BEING_SERVED", description="Patient done being served by reception staff."
    )
