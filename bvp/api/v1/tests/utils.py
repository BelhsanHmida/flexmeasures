"""Useful test messages"""


def message_for_get_meter_data(
    no_connection: bool = False,
    invalid_connection: bool = False,
    single_connection=False,
    invalid_unit: bool = False,
    no_unit: bool = False,
) -> dict:
    message = {
        "type": "GetMeterDataRequest",
        "start": "2015-01-01T00:00:00Z",
        "duration": "PT1H30M",
        "connections": ["CS 1", "CS 2", "CS 3"],
        "unit": "MW",
    }
    if no_connection:
        message.pop("connections", None)
    elif invalid_connection:
        message["connections"] = ["Non-existing asset 1", "Non-existing asset 2"]
    elif single_connection:
        message["connection"] = message["connections"][0]
        message.pop("connections", None)
    if no_unit:
        message.pop("unit", None)
    elif invalid_unit:
        message["unit"] = "MW/h"
    return message


def message_for_post_meter_data(
    no_connection: bool = False,
    single_connection: bool = False,
    single_connection_group: bool = False,
) -> dict:
    message = {
        "type": "PostMeterDataRequest",
        "groups": [
            {
                "connections": ["CS 1", "CS 2"],
                "values": [306.66, 306.66, 0, 0, 306.66, 306.66],
            },
            {"connection": ["CS 3"], "values": [306.66, 0, 0, 0, 306.66, 306.66]},
        ],
        "start": "2015-01-01T00:00:00Z",
        "duration": "PT1H30M",
        "unit": "MW",
    }
    if no_connection:
        message.pop("groups", None)
    elif single_connection:
        message["connection"] = message["groups"][0]["connections"][0]
        message["values"] = message["groups"][1]["values"]
        message.pop("groups", None)
    elif single_connection_group:
        message["connections"] = message["groups"][0]["connections"]
        message["values"] = message["groups"][0]["values"]
        message.pop("groups", None)

    return message


def count_connections_in_post_message(message: dict) -> int:
    connections = 0
    if "groups" in message:
        message = dict(
            connections=message["groups"][0]["connections"],
            connection=message["groups"][1]["connection"],
        )
    if "connection" in message:
        connections += 1
    if "connections" in message:
        connections += len(message["connections"])
    return connections