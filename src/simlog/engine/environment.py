import gc
import typing
from heapq import heappop
from typing import Optional

from simpy import Environment

if typing.TYPE_CHECKING:
    from simlog.engine import ComponentManager


class UnsetManager(Exception):
    """Thrown by an :class:`Environment` if the manager attribute
    has not been set."""


class EmptySchedule(Exception):
    """Thrown by an :class:`Environment` if there are no further events to be
    processed."""


class DummyEnvironment(Environment):
    """Used where an environment is expected, but not actually used."""

    def step(self) -> None:
        """Should not be called when using the dummy environment."""
        raise NotImplementedError("Trying to step in a dummy environment.")


class SimLogEnvironment(Environment):
    """
    Modified Simpy environment with observer pattern to allow
    particular components to listen to particular events.
    """

    def __init__(self, *args, manager: Optional["ComponentManager"] = None, event_logging: bool = True, **kwargs):
        """
        Constructor for the SimLog Environment.

        Args:
            manager (:obj:`ComponentManager`, optional): Manager for the event observer pattern.
        """
        super().__init__(*args, **kwargs)
        self.manager = manager
        self.event_logging = event_logging

        # Why do we need additional garbage collector when we have reference counting?
        # Unfortunately, classical reference counting has a fundamental problem — it cannot
        # detect reference cycles. A reference cycle occurs when one or more objects are
        # referencing each other.
        # In SimpyLog, this is a problem with the references between env, manager and manager.event_log.
        # The memory leak occurs during multiruns.
        gc.collect()

    def step(self) -> None:
        """Process the next event.

        Raise an :exc:`EmptySchedule` if no further events are available.

        """

        # This is the updated part of the step method.
        if self.manager is None:
            raise UnsetManager("Set the manager attribute")
        if len(self._queue):
            t, prio, eid, event = self._queue[0]
            self.manager.trigger_event(event=event)
            if self.event_logging:
                self.manager.log_event(self._queue[0])
        # This is the end of the updated code.
        try:
            self._now, _, _, event = heappop(self._queue)
        except IndexError:
            raise EmptySchedule()

        # Process callbacks of the event. Set the events callbacks to None
        # immediately to prevent concurrent modifications.
        callbacks, event.callbacks = event.callbacks, None  # type: ignore
        for callback in callbacks:
            callback(event)

        if not event._ok and not hasattr(event, "_defused"):
            # The event has failed and has not been defused. Crash the
            # environment.
            # Create a copy of the failure exception with a new traceback.
            exc = type(event._value)(*event._value.args)
            exc.__cause__ = event._value
            raise exc
