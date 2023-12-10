from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING
from uuid import UUID

from simpy import Event, Interrupt
from simpy.events import EventCallbacks, Initialize, Timeout

from simlog.data_models import LoggedEvent
from simlog.events.events import (
    BaseSimLogEvent,
    EventTopic,
    SimLogInitialize,
    SimLogProcess,
    SimLogSingleRefEvent,
    SimLogTargetedTimeout,
    SimLogTimeout,
    SimLogUuidRefEvent,
)
from src.simlog.engine.base import BaseComponent

if TYPE_CHECKING:
    from simlog.engine import SimLogEnvironment


class ComponentManager:
    """
    Component manager is aware of all components.

    It provides the trigger_event method which is patched into env.step to allow components
    to listen for relevant events
    """

    def __init__(
        self,
        *,
        env: "SimLogEnvironment",
        components: Sequence[BaseComponent] | None = None,
    ):
        self.env = env
        self._components = None
        self.components = components
        self.event_log: list = []

    def trigger_event(self, event: Event):
        """Method to be patched into env.step."""
        if not self.components:
            return
        if isinstance(event, SimLogProcess):
            if hasattr(event, "single_reference"):
                event.callbacks.append(self._component_lookup[event.single_reference].listen)
            else:
                topic = getattr(event, "topic", None)
                if topic is not None:
                    event.callbacks += self._subscriptions_lookup[topic]
        elif isinstance(event, (SimLogTargetedTimeout | SimLogUuidRefEvent)):
            event.callbacks.append(self._component_lookup[event.single_reference].listen)
        elif isinstance(event, (SimLogSingleRefEvent)):
            event.callbacks.append(event.single_reference.listen)
        elif isinstance(event, (SimLogTimeout | SimLogInitialize | BaseSimLogEvent)):
            topic = getattr(event, "topic", None)
            if topic is not None:
                event.callbacks += self._subscriptions_lookup[topic]

    def log_event(self, event: Event):
        """
        Append event details to the sequence maintained by the manager.
        Reminder of simpy event structure:
        (self._now + delay, priority, next(self._eid), event))

        Args:
            event (:obj:`Event`): A SimLog event.
        """
        topic = None
        parent = None
        single_reference = None
        component_state = None

        _event = event[3]
        if isinstance(_event, (Initialize | Timeout)):
            return
        if isinstance(_event, (BaseSimLogEvent | SimLogSingleRefEvent | SimLogProcess | SimLogInitialize)):
            topic = _event.topic.value if _event.topic else None
            if isinstance(_event.parent, UUID) and _event.parent:
                parent = self.get_component_name_by_uuid(_event.parent)
            elif _event.parent and isinstance(_event.parent, str):
                parent = _event.parent
            elif _event.parent:
                parent = _event.parent.name
            else:
                parent = None
            if hasattr(_event, "component_state") and _event.component_state:
                component_state = _event.component_state.value

        if topic is None:
            return

        if isinstance(_event, (SimLogSingleRefEvent)) and isinstance(_event.single_reference, UUID):
            single_reference = self.get_component_name_by_uuid(_event.single_reference)
        elif isinstance(_event, (SimLogSingleRefEvent)):
            single_reference = _event.single_reference.name if _event.single_reference else None
        elif isinstance(_event, (SimLogUuidRefEvent)) and isinstance(_event.single_reference, UUID):
            single_reference = self.get_component_name_by_uuid(_event.single_reference)

        if isinstance(_event.value, BaseComponent):
            value = _event.value.name
        elif isinstance(_event.value, UUID):
            value = self.get_component_name_by_uuid(_event.value)
        elif isinstance(_event.value, Interrupt):
            value = {"interruption cause": _event.value.cause}
        else:
            value = _event.value

        self.event_log.append(
            LoggedEvent(
                topic=topic.value,
                parent=parent,
                single_reference=single_reference,
                sim_time=event[0],
                value=value,
                simpy_id=event[2],
                simpy_priority=event[1],
                component_state=component_state,
            )
        )

    @property
    def components(self) -> Sequence[BaseComponent] | None:
        """Components property getter."""
        return self._components

    @components.setter
    def components(self, components: list[BaseComponent]):
        """Sets the list of components in the simulation."""
        self._components = components

        if components is not None:
            # A lookup from component uuid to component.
            self._component_lookup: dict[UUID, BaseComponent] = {}
            # A lookup from event topic to component listen functions for components that are subscribed to that event type.
            self._subscriptions_lookup: dict[EventTopic, EventCallbacks] = defaultdict(list)

            for component in components:
                # Add the lookup from UUID to component
                self._component_lookup[component.uuid] = component

                # Add the lookup from event topic to component listen function
                for topic in component.subscriptions:
                    self._subscriptions_lookup[topic].append(component.listen)
        else:
            self._component_lookup = {}
            self._subscriptions_lookup = defaultdict(list)

    def get_component_by_uuid(self, id: UUID) -> BaseComponent | None:
        """Fetch component object by its UUID."""
        return self._component_lookup.get(id)

    def get_component_name_by_uuid(self, id: UUID) -> str | None:
        """Fetch component name by its UUID."""
        component = self._component_lookup.get(id)
        return component.name if component else None
