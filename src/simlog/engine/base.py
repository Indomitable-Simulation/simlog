import uuid
from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any
from uuid import UUID

from simpy import Event
from simpy.core import ProcessGenerator

from simlog.events.events import (
    BaseSimLogEvent,
    EventTopic,
    SimLogProcess,
    SimLogTargetedTimeout,
    SimLogTimeout,
    SimLogUuidRefEvent,
)

if TYPE_CHECKING:
    from simlog.engine.environment import SimLogEnvironment

SUPPORTED_EVENTS = [BaseSimLogEvent, SimLogProcess, SimLogTargetedTimeout, SimLogTimeout, SimLogUuidRefEvent]


class BaseComponent:
    """
    Base class all Components inherit from.

    Contains a number of helper methods and abstractions
    for creating and listening for simulation events.
    """

    def __init__(
        self,
        env: "SimLogEnvironment",
        unique_id: UUID | None = None,
        subscriptions: Sequence[EventTopic] | None = None,
        name: str | None = None,
    ) -> None:
        """
        Constructor for the BaseComponent
        Args:
            env (SimLogEnvironment): Simulation environment, responsible for the core sim loop.
            unique_id (UUID, optional): Identifier for the component.
            subscriptions (:obj:`list` of :obj:`EventTopic`, optional): Topics the component subscribes to.
            name (str, optional): Component name.
        """
        self.env = env
        self._subscriptions = subscriptions
        if subscriptions is None:
            self._subscriptions = []
        self.uuid = unique_id if unique_id else uuid.uuid4()
        self.name = name if name else self.__class__.__name__
        self.last_time_state_updated = self.env.now
        self.state: str | None = None

    @abstractmethod
    def listen(self, event: Event, *args, **kwargs):
        """Determines actions given a particular event."""
        ...

    @property
    def subscriptions(self) -> Sequence[EventTopic] | None:
        """Access component subscriptions."""
        return self._subscriptions

    @subscriptions.setter
    def subscriptions(self, subscriptions: Sequence[EventTopic]) -> None:
        """Set component subscriptions."""
        self._subscriptions = subscriptions

    def update_state(self, new_state: str, location: UUID | str | None = None):
        """This function updates the state of a component.

        It then publishes a corresponding event for the state update.

        If there is no change in state the event will not be published.

        Parameters
         ----------
        new_state : any
            The new state name.
        location : Union[UUID, str], default None
            Reference to a component that is the location of the state change.
        """
        if isinstance(location, UUID):
            location = self.env.manager.get_component_name_by_uuid(location)
        else:
            location = location
        if new_state is self.state:
            # do nothing - no change in state
            pass

        else:
            # update state and log event
            self.state = new_state

            event_topic = EventTopic.STATE_CHANGE

            event = BaseSimLogEvent(
                env=self.env,
                topic=event_topic,
                parent=self.uuid,
            )
            event.component_state = self.state
            event.succeed(value=location)

    def start_process(
        self,
        generator: ProcessGenerator,
        start_topic: EventTopic,
        end_topic: EventTopic,
        target: UUID | None = None,
    ):
        """Process an event yielding generator with SimLog event attributes

        Args:
            generator: ProcessGenerator
            start_topic: EventTopic - the topic of the event that initialises the process
            end_topic: EventTopic - the topic of the Process event - i.e. the event processed
                when the process is complete
            target: UUID of component to be notified when the process is finished
        """
        return SimLogProcess(
            env=self.env,
            generator=generator,
            start_topic=start_topic,
            end_topic=end_topic,
            parent=self.uuid,
            target=target,
        )

    def create_event(
        self,
        topic: EventTopic,
        target: UUID | None = None,
        cause: Event | None = None,
        value: Any | None = None,
        timeout: int | None = None,
    ):
        """Create and schedule a SimLog event

        Arguments:
        topic: EventTopic - event topic of the event
        target: UUID of component to be notified when the event is processed
        cause: Event - an event to be passed at the event cause
        value: Any - value of the event, passed to succeed method
        delay: Numeric - number of simulation seconds to wait until the event is processed

        - If neither target nor delay are provided create a BaseSimLogEvent
        - If target but not delay is provided, create a SimLogUuidRefEvent
        - If delay but not target is provided, create a SimLogTimeout
        - If delay and target are provided, create a SimLogTargetedTimeout
        - pass cause to events
        """
        if not (target or timeout):
            return BaseSimLogEvent(env=self.env, topic=topic, parent=self.uuid, cause=cause).succeed(value)
        if not timeout:
            return SimLogUuidRefEvent(
                env=self.env,
                topic=topic,
                single_reference=target,
                parent=self.uuid,
                cause=cause,
            ).succeed(value)
        if timeout and not target:
            return SimLogTimeout(
                env=self.env,
                delay=timeout,
                topic=topic,
                parent=self.uuid,
                value=value,
                cause=cause,
            )
        if timeout and target:
            return SimLogTargetedTimeout(
                env=self.env,
                delay=timeout,
                topic=topic,
                single_reference=target,
                parent=self.uuid,
                value=value,
                cause=cause,
            )
        raise ValueError("Sorry you can't specify that kind of event yet.")
