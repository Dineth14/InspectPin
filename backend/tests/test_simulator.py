from simulator.inspectpin_simulator import SimulatorState, VirtualInspectPin


def test_simulator_wave_and_fault_state():
    state = SimulatorState("http://127.0.0.1:5000", "user", "sim-1", "device", online=False)
    device = VirtualInspectPin(state)
    wav = device.mock_wav(0.25)
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    assert len(wav) == 8044
    try:
        device.heartbeat()
    except RuntimeError as exc:
        assert "SIMULATED_OFFLINE" in str(exc)
    else:
        raise AssertionError("Offline simulator unexpectedly used the network")
