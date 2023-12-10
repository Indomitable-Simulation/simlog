# SimLog - Get More From Your Discrete Event Simulations
A [SimPy](https://simpy.readthedocs.io/en/latest/) extension providing:
- Typed events (via [Pydantic](https://docs.pydantic.dev/latest/))
- Event log persistence
- [Publish-Subscribe](https://en.wikipedia.org/wiki/Publish%E2%80%93subscribe_pattern)-like* functionality
for decoupling simulation components and allowing them to react to events.
- [Optional] stateful components

*Technically this is done via the [observer pattern](https://en.wikipedia.org/wiki/Observer_pattern) via
the component manager.


### Conceptual Overview
SimLog (short for SimPy Event Log) was inspired by [this discussion & code snippet](https://simpy.readthedocs.io/en/latest/topical_guides/monitoring.html#event-tracing) in the Simpy docs.

> In order to debug or visualize a simulation, you might want to trace when events are created, triggered and processed. Maybe you also want to trace which process created an event and which processes waited for an event.

The extension's fundamental value-add is to subclass the Simpy `Environment` and overriding the `Environment`'s `step` method, enabling:
1. Logging events 
2. Having simulation components subscribe to particular events

In the age of LLMs, another key use-case for generating an event log is to generate data to pass to an LLM for analysis.


### How to Use Simpy Eventlog

#### Setup
1. [Mandatory] Define your simulation's events if applicable using the `EventTopicValue`
2. [Mandatory] Create your simulation's components (from the `BaseComponent`). Your
simulation components must define a `listen` method to define how they react to events. One
or more components will need to create some initial events to kick off the simulation in its
`__init__` method.

#### Running
- Instantiate the `SimLogEnvironment`
- Instantiate your simulation components, specifying any event subscriptions
- Instantiate your `ComponentManager` and register your components
- Attach your `ComponentManager` to the `SimLogEnvironment`.

That's it - you will now have an event log output.

For examples see the `examples` directory.


### Event Log Default Persistence
- Default: .json file
- Optional: sqlite [TODO]

*Warning, for long-running simulation, these files can be large.


### TO FIGURE OUT [WIP]
- How to enable easy usage of the simpy primitives like Resources?
- Do we want processor / component separation?
- The events are super confusing
- If components are passed around, it creates serialization issues. Currently hacked
via `Loggable` mixin, but this feels ugly
- Should all components subscribe to an `STATE_CHANGE` event? Do we event want to include state
management?
- Do we want to define a clear config format?
