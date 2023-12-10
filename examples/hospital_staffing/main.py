from os import mkdir
from pathlib import Path

from simlog.data_models.event_log import EventLog
from simlog.engine.component_manager import ComponentManager
from simlog.engine.environment import SimLogEnvironment

from examples.hospital_staffing.components import Patient, Reception
from examples.hospital_staffing.events import EventTopic

NUM_RECEPTIONISTS = 2


def generate_patients(env: SimLogEnvironment):
    return [Patient(env=env, name=entry) for entry in range(10)]


def main():
    # TODO: Ensure output path exists.
    # create directory if it does not exist
    if not Path("output").exists():
        mkdir("output")

    env = SimLogEnvironment()
    reception = Reception(env=env, subscriptions=[EventTopic.PATIENT_JOINED_QUEUE, EventTopic.PATIENT_ARRIVED_AT_DESK])
    patients = generate_patients(env=env)
    manager = ComponentManager(env=env, components=[reception] + patients)
    env.manager = manager
    env.run(until=60*60)

    print("Simulation run complete.")
    event_log = EventLog(logs=env.manager.event_log)
    event_log.json_dump(path=Path("output/event_log.json"), event_topic=EventTopic)


if __name__ == "__main__":
    main()
