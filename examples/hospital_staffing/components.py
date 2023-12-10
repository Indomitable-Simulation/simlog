import random
from enum import Enum

from simlog.data_models.event_log import Loggable
from simlog.engine import BaseComponent, SimLogEnvironment
from simlog.events.events import BaseSimLogEvent
from simpy import Resource

from examples.hospital_staffing.events import EventTopic


class IssueTypes(Enum):
    CHEST_PAIN = "Chest pain"
    BROKEN_BONE = "Broken bone"
    WANTS_DIRECTIONS = "Wants Directions"


class Patient(BaseComponent, Loggable):
    def __init__(self, env: SimLogEnvironment, name: str = None, subscriptions=None, **kwargs):
        super().__init__(env, subscriptions=subscriptions, **kwargs)
        self.issue = random.choice(list(IssueTypes))
        self.id = name
        BaseSimLogEvent(env=env, topic=EventTopic.PATIENT_JOINED_QUEUE, parent=None).succeed(self)

    def get_loggable_data(self):
        return {"id": str(self.id), "issue": self.issue.value if self.issue else None}


class Reception(BaseComponent):
    def __init__(self, env: SimLogEnvironment, subscriptions=None, **kwargs):
        super().__init__(env, subscriptions=subscriptions, **kwargs)
        self.reception = Resource(env, capacity=1)

    def listen(self, event: BaseSimLogEvent, *args, **kwargs):
        if event.topic == EventTopic.PATIENT_ARRIVED_AT_DESK:
            self.env.process(self.serve_patient(patient=event.value))
        if event.topic == EventTopic.PATIENT_JOINED_QUEUE:
            self.env.process(self.wait_in_line(patient=event.value))

    def serve_patient(self, patient: Patient):
        """The time it takes to serve a patient depends on their issue."""
        with self.reception.request() as request:
            yield request
            print(f"{self.env.now}: Patient {patient.id} is being served.")
            time_taken = 0
            if patient.issue == IssueTypes.CHEST_PAIN:
                time_taken = 60
            if patient.issue == IssueTypes.BROKEN_BONE:
                time_taken = 300
            if patient.issue == IssueTypes.WANTS_DIRECTIONS:
                time_taken = 10
            print(f"{self.env.now}: Patient {patient.id} is talking to reception.")
            yield self.env.timeout(delay=time_taken)
            print(f"{self.env.now}: Patient {patient.id} has left reception.")

    def wait_in_line(self, patient: Patient):
        """Check if the resource is available."""
        with self.reception.request() as request:
            yield request  # Wait until the reception resource becomes available
            print(f"At time {self.env.now}, Patient {patient.id} joined the queue.")
            return BaseSimLogEvent(env=self.env, topic=EventTopic.PATIENT_ARRIVED_AT_DESK, parent=None).succeed(patient)
