import typing
from enum import Enum
from typing import Any, Union
from uuid import UUID

from pydantic import BaseModel
from simpy.core import ProcessGenerator
from simpy.events import NORMAL, URGENT, Event, EventCallbacks, Process

if typing.TYPE_CHECKING:
    from simlog.engine import BaseComponent, SimLogEnvironment


class EventTopicValue(BaseModel):
    value: Any
    description: str


class EventTopic(Enum):
    """List of possible events."""

    # TODO: Provide interface to define these
    DUMMY_EVENT = EventTopicValue(value="DUMMY_EVENT", description="Example event")
    STATE_CHANGE = EventTopicValue(value="STATE_CHANGE", description="Used by all components")


class BaseSimLogEvent(Event):
    """Base SimLog event which modifies the Simpy Event for the observer pattern."""

    def __init__(
        self,
        *,
        env: "SimLogEnvironment",
        topic: EventTopic | None,
        parent: Union["BaseComponent", UUID, None] = None,
        cause: Event | None = None,
    ) -> None:
        """Constructor for the BaseSimLogEvent class."""
        super().__init__(env=env)
        self.topic = topic
        self.parent = parent
        self.component_state = None
        self.cause = cause


class SimLogTimeout(BaseSimLogEvent):
    """A SimLogEvent that gets triggered after a *delay* has passed."""

    def __init__(
        self,
        env: "SimLogEnvironment",
        delay: int,
        topic: EventTopic | None,
        parent: UUID | None,
        value: Any | None = None,
        cause: Event | None = None,
    ):
        """Constructor for the SimLogTimeout class."""
        super().__init__(env=env, topic=topic, parent=parent, cause=cause)
        self._value = value
        self._ok = True
        if delay < 0:
            raise ValueError(f"Negative delay {delay}")
        env.schedule(self, NORMAL, delay)


class SimLogTargetedTimeout(SimLogTimeout):
    """A SimLogEvent that gets triggered after a *delay* has passed, notifying a particular component."""

    def __init__(
        self,
        env: "SimLogEnvironment",
        delay: int,
        topic: EventTopic | None,
        parent: UUID | None,
        single_reference: UUID | None = None,
        value: Any | None = None,
        cause: Event | None = None,
    ):
        """Constructor for the SimLogTargetedTimeout class."""
        super().__init__(env=env, delay=delay, topic=topic, parent=parent, value=value, cause=cause)
        self.single_reference = single_reference


class SimLogSingleRefEvent(BaseSimLogEvent):
    """Event which targets a specific component."""

    def __init__(
        self,
        *,
        env: "SimLogEnvironment",
        topic: EventTopic,
        single_reference: Any,  # TODO: update type
        parent: Any | None = None,
        cause: Event | None = None,
    ) -> None:
        """Constructor for the SimLogSingleRefEvent class."""
        super().__init__(env=env, topic=topic, parent=parent)
        self.single_reference = single_reference
        self.cause = cause


class SimLogUuidRefEvent(BaseSimLogEvent):
    """Event that targets a specific component via UUID."""

    def __init__(
        self,
        *,
        env: "SimLogEnvironment",
        topic: EventTopic,
        single_reference: UUID | None,
        parent: Any | None = None,
        cause: Event | None = None,
    ) -> None:
        """Constructor for the SimLogUuidRefEvent class."""
        super().__init__(env=env, topic=topic, parent=parent)
        self.single_reference = single_reference
        self.cause = cause


class SimLogProcess(Process):
    """Process an event yielding generator with SimLog event attributes."""

    def __init__(
        self,
        env: "SimLogEnvironment",
        generator: ProcessGenerator,
        start_topic: EventTopic,
        end_topic: EventTopic,
        parent: UUID,
        target: UUID | None = None,
    ):
        """
        Constructor for the SimLogProcess class.
        """

        if not hasattr(generator, "throw"):
            raise ValueError(f"{generator} is not a generator.")

        self.env = env
        self.parent = parent
        self.callbacks: EventCallbacks = []

        self._generator = generator

        self._target: Event = SimLogInitialize(env, self, start_topic, parent)
        self.topic = end_topic
        if target is not None:
            self.single_reference = target


class SimLogInitialize(BaseSimLogEvent):
    """Initializes a SimLogProcess process."""

    def __init__(self, env: "SimLogEnvironment", process: "Process", topic: EventTopic, parent: UUID):
        """
        Constructor for the SimLogInitialize class.
        """

        self.topic = topic
        super().__init__(env=env, topic=topic, parent=parent)
        self.callbacks: EventCallbacks = [process._resume]
        self._value: Any = None
        self._ok = True
        env.schedule(self, URGENT)
