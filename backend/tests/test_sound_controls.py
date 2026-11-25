from test_product_api import account, paired


def test_requested_sound_is_confirmed_only_after_device_ack(factory):
    client = factory().test_client()
    owner, other = account(client), account(client, "other@example.test")
    device = paired(client, owner)
    root = "/api/v1/devices/sim-unit-01"
    initial = {"groups": 127, "volume": 65, "speech_volume": 100}
    metadata = {"version": "1.1.0", "build": "test-build", "boot_slot": "app0", "ota_enabled": False}
    heartbeat = client.post("/api/v1/device/heartbeat", headers=device, json={
        "sound_settings": initial, "reported_firmware": metadata,
    })
    assert heartbeat.status_code == 200
    status = client.get(root + "/status", headers=owner).json
    assert status["firmware_version"] == "sim-1.0"
    assert status["reported_firmware"]["version"] == "1.1.0"
    assert status["sound_settings"] == initial

    requested = {"type": "set_sound", "payload": {"groups": 9, "volume": 35}}
    assert client.post(root + "/commands", headers=other, json=requested).status_code == 404
    for invalid in (True, -1, 101, "50"):
        bad = {"type": "set_sound", "payload": {"groups": 9, "volume": invalid}}
        assert client.post(root + "/commands", headers=owner, json=bad).status_code == 400
    queued = client.post(root + "/commands", headers=owner, json=requested)
    assert queued.status_code == 201
    assert client.get(root + "/status", headers=owner).json["sound_settings"] == initial

    actual = {**requested["payload"], "speech_volume": 100}
    ack = client.post(f"/api/v1/device/commands/{queued.json['id']}/ack", headers=device, json={
        "status": "completed", "result": {"sound_settings": actual},
    })
    assert ack.status_code == 200
    assert client.get(root + "/status", headers=owner).json["sound_settings"] == actual
