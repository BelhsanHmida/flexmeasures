from __future__ import annotations

import pytest
from flask import url_for


from flexmeasures import Sensor
from flexmeasures.api.tests.utils import get_auth_token
from flexmeasures.api.v3_0.tests.utils import get_sensor_post_data
from flexmeasures.data.schemas.sensors import SensorSchema

sensor_schema = SensorSchema()


def test_fetch_one_sensor(
    client,
    setup_api_test_data: dict[str, Sensor],
):
    sensor_id = 1
    headers = make_headers_for("test_supplier_user_4@seita.nl", client)
    response = client.get(
        url_for("SensorAPI:fetch_one", id=sensor_id),
        headers=headers,
    )
    print("Server responded with:\n%s" % response.json)
    assert response.status_code == 200
    assert response.json["name"] == "some gas sensor"
    assert response.json["unit"] == "m³/h"
    assert response.json["generic_asset_id"] == 4
    assert response.json["timezone"] == "UTC"
    assert response.json["event_resolution"] == "PT10M"


@pytest.mark.parametrize("use_auth", [False, True])
def test_fetch_one_sensor_no_auth(
    client, setup_api_test_data: dict[str, Sensor], use_auth
):
    """Test 1: Sensor with id 1 is not in the test_prosumer_user_2@seita.nl's account.
    The Supplier Account as can be seen in flexmeasures/api/v3_0/tests/conftest.py
    Test 2: There is no authentication int the headers"""
    sensor_id = 1
    if use_auth:
        headers = make_headers_for("test_prosumer_user_2@seita.nl", client)
        response = client.get(
            url_for("SensorAPI:fetch_one", id=sensor_id),
            headers=headers,
        )
        assert response.status_code == 403
        assert (
            response.json["message"]
            == "You cannot be authorized for this content or functionality."
        )
        assert response.json["status"] == "INVALID_SENDER"
    else:
        headers = make_headers_for(None, client)
        response = client.get(
            url_for("SensorAPI:fetch_one", id=sensor_id),
            headers=headers,
        )
        assert response.status_code == 401
        assert (
            response.json["message"]
            == "You could not be properly authenticated for this content or functionality."
        )
        assert response.json["status"] == "UNAUTHORIZED"


def make_headers_for(user_email: str | None, client) -> dict:
    headers = {"content-type": "application/json"}
    if user_email:
        headers["Authorization"] = get_auth_token(client, user_email, "testtest")
    return headers


def test_post_a_sensor(client, setup_api_test_data):
    auth_token = get_auth_token(client, "test_admin_user@seita.nl", "testtest")
    post_data = get_sensor_post_data()
    response = client.post(
        url_for("SensorAPI:post"),
        json=post_data,
        headers={"content-type": "application/json", "Authorization": auth_token},
    )
    print("Server responded with:\n%s" % response.json)
    assert response.status_code == 201
    assert response.json["name"] == "power"
    assert response.json["event_resolution"] == "PT1H"

    sensor: Sensor = Sensor.query.filter_by(name="power").one_or_none()
    assert sensor is not None
    assert sensor.unit == "kWh"


def test_post_sensor_to_asset_from_unrelated_account(client, setup_api_test_data):
    """Tries to add sensor to account the user doesn't have access to"""
    auth_token = get_auth_token(client, "test_supplier_user_4@seita.nl", "testtest")
    post_data = get_sensor_post_data()
    response = client.post(
        url_for("SensorAPI:post"),
        json=post_data,
        headers={"content-type": "application/json", "Authorization": auth_token},
    )
    print("Server responded with:\n%s" % response.json)
    assert response.status_code == 403
    assert (
        response.json["message"]
        == "You cannot be authorized for this content or functionality."
    )
    assert response.json["status"] == "INVALID_SENDER"