"""
test_simulator.py
=================
Automated unit tests for Lamport Logical Clock algorithm and simulation engine.
"""

import pytest
from lamport_clock import LamportProcess, EventType
from simulator import SimulationEngine, EventSpec


def test_lamport_process_direct_rules():
    """Test Lamport clock state updates on an individual process."""
    p1 = LamportProcess("P1")
    assert p1.clock == 0

    # Rule 1: Internal event
    e1 = p1.execute_internal("E1")
    assert e1.prev_clock == 0
    assert e1.clock == 1
    assert p1.clock == 1

    # Rule 2: Send event
    e2, msg = p1.execute_send("E2", "M1", "P2")
    assert e2.prev_clock == 1
    assert e2.clock == 2
    assert msg.sent_timestamp == 2
    assert p1.clock == 2

    # Rule 3: Receive event on P2
    p2 = LamportProcess("P2")
    e3 = p2.execute_internal("E3")  # clock becomes 1
    assert e3.clock == 1

    e4 = p2.execute_receive("E4", msg)
    # C = max(1, 2) + 1 = 3
    assert e4.prev_clock == 1
    assert e4.received_timestamp == 2
    assert e4.clock == 3
    assert p2.clock == 3


def test_preset_1_college_demo():
    """Test the complete college viva demo preset scenario."""
    sim = SimulationEngine.load_preset_1_college_demo()
    is_valid, errors, warnings = sim.validate()
    assert is_valid, f"Validation failed with errors: {errors}"
    assert len(errors) == 0

    res = sim.run()
    event_dict = {e.event_id: e for e in res.events}

    # Verify all Lamport clock calculations dynamically
    assert event_dict["E1"].clock == 1  # P1 internal: 0 + 1 = 1
    assert event_dict["E2"].clock == 2  # P1 send M1: 1 + 1 = 2
    assert event_dict["E3"].clock == 1  # P2 internal: 0 + 1 = 1
    assert event_dict["E4"].clock == 3  # P2 receive M1: max(1, 2) + 1 = 3
    assert event_dict["E5"].clock == 1  # P3 internal: 0 + 1 = 1
    assert event_dict["E6"].clock == 2  # P3 send M2: 1 + 1 = 2
    assert event_dict["E7"].clock == 3  # P1 receive M2: max(2, 2) + 1 = 3

    # Check Total Order:
    # Clock 1: E1 (P1), E3 (P2), E5 (P3)
    # Clock 2: E2 (P1), E6 (P3)
    # Clock 3: E7 (P1), E4 (P2)
    order_ids = [e.event_id for e in res.total_order]
    assert order_ids == ["E1", "E3", "E5", "E2", "E6", "E7", "E4"]

    # Check Causality
    cm = res.causality_matrix
    assert "Happened Before" in cm[("E1", "E2")]
    assert "Happened Before" in cm[("E2", "E4")]
    assert "Happened Before" in cm[("E1", "E4")]  # Transitivity
    assert "Happened Before" in cm[("E5", "E6")]
    assert "Happened Before" in cm[("E6", "E7")]
    assert "Happened Before" in cm[("E5", "E7")]  # Transitivity
    assert "Concurrent" in cm[("E1", "E3")]
    assert "Concurrent" in cm[("E1", "E5")]
    assert "Concurrent" in cm[("E3", "E5")]
    assert "Concurrent" in cm[("E4", "E6")]


def test_preset_2_pipeline():
    """Test 4-process pipeline preset."""
    sim = SimulationEngine.load_preset_2_four_processes_cascade()
    is_valid, errors, _ = sim.validate()
    assert is_valid
    res = sim.run()
    event_dict = {e.event_id: e for e in res.events}
    assert event_dict["E1"].clock == 1
    assert event_dict["E2"].clock == 2
    assert event_dict["E3"].clock == 3
    assert event_dict["E4"].clock == 4
    assert event_dict["E5"].clock == 5
    assert event_dict["E6"].clock == 6
    assert event_dict["E7"].clock == 7
    assert event_dict["E8"].clock == 8


def test_validation_errors():
    """Test various validation failure triggers."""
    # 1. Duplicate Event ID
    sim1 = SimulationEngine(["P1", "P2"])
    sim1.add_event(EventSpec("E1", "P1", EventType.INTERNAL))
    sim1.add_event(EventSpec("E1", "P1", EventType.INTERNAL))
    is_valid, errors, _ = sim1.validate()
    assert not is_valid
    assert any("Duplicate Event ID" in err for err in errors)

    # 2. Receive before send
    sim2 = SimulationEngine(["P1", "P2"])
    sim2.add_event(EventSpec("E1", "P2", EventType.RECEIVE, message_id="M1", source_process="P1"))
    sim2.add_event(EventSpec("E2", "P1", EventType.SEND, message_id="M1", target_process="P2"))
    is_valid, errors, _ = sim2.validate()
    assert not is_valid
    assert any("Causality Violation" in err or "never sent" in err for err in errors)

    # 3. Receive without send
    sim3 = SimulationEngine(["P1", "P2"])
    sim3.add_event(EventSpec("E1", "P2", EventType.RECEIVE, message_id="M99", source_process="P1"))
    is_valid, errors, _ = sim3.validate()
    assert not is_valid
    assert any("never sent" in err for err in errors)

    # 4. Send to self
    sim4 = SimulationEngine(["P1", "P2"])
    sim4.add_event(EventSpec("E1", "P1", EventType.SEND, message_id="M1", target_process="P1"))
    is_valid, errors, _ = sim4.validate()
    assert not is_valid
    assert any("same process" in err for err in errors)
