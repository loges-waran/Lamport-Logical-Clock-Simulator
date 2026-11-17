"""
simulator.py
============
Simulation engine for Lamport's Logical Clock algorithm.
Handles event validation, dynamic execution, step-by-step trace generation,
happens-before causality analysis, and total ordering.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
from lamport_clock import LamportProcess, Event, Message, EventType


@dataclass
class EventSpec:
    """Specification of an event defined by the user prior to execution."""
    event_id: str
    process_id: str
    event_type: EventType
    message_id: Optional[str] = None
    target_process: Optional[str] = None
    source_process: Optional[str] = None
    custom_desc: str = ""

    def summary(self) -> str:
        if self.event_type == EventType.INTERNAL:
            return f"[{self.event_id}] {self.process_id}: Internal Event"
        elif self.event_type == EventType.SEND:
            return f"[{self.event_id}] {self.process_id}: Send {self.message_id} -> {self.target_process}"
        elif self.event_type == EventType.RECEIVE:
            return f"[{self.event_id}] {self.process_id}: Receive {self.message_id} <- {self.source_process}"
        return f"[{self.event_id}] {self.process_id}: {self.event_type}"


@dataclass
class SimulationResult:
    """Stores full output of a simulation execution."""
    events: List[Event] = field(default_factory=list)
    messages: Dict[str, Message] = field(default_factory=dict)
    process_clocks: Dict[str, int] = field(default_factory=dict)
    process_events: Dict[str, List[Event]] = field(default_factory=dict)
    total_order: List[Event] = field(default_factory=list)
    causality_matrix: Dict[Tuple[str, str], str] = field(default_factory=dict)
    step_snapshots: List[Dict] = field(default_factory=list)


class SimulationEngine:
    """
    Main simulator orchestrator that validates event schedules,
    executes Lamport clocks dynamically, and evaluates causality.
    """

    def __init__(self, process_ids: Optional[List[str]] = None):
        self.process_ids = process_ids if process_ids else ["P1", "P2", "P3"]
        self.event_specs: List[EventSpec] = []

    def set_processes(self, process_ids: List[str]) -> None:
        """Update configured processes and filter out events from removed processes."""
        self.process_ids = process_ids
        self.event_specs = [e for e in self.event_specs if e.process_id in process_ids]

    def add_event(self, spec: EventSpec) -> None:
        """Append an event specification."""
        self.event_specs.append(spec)

    def remove_event(self, index: int) -> None:
        """Remove event by index."""
        if 0 <= index < len(self.event_specs):
            self.event_specs.pop(index)

    def clear(self) -> None:
        """Clear all event specifications."""
        self.event_specs.clear()

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        Validate the event specifications.
        Returns:
            (is_valid, errors_list, warnings_list)
        """
        errors: List[str] = []
        warnings: List[str] = []

        if not self.event_specs:
            return False, ["No events configured. Add events or load a preset."], []

        # 1. Check duplicate Event IDs
        seen_events: Set[str] = set()
        for idx, spec in enumerate(self.event_specs):
            if not spec.event_id or spec.event_id.strip() == "":
                errors.append(f"Event at row #{idx + 1} has an empty Event ID.")
            elif spec.event_id in seen_events:
                errors.append(f"Duplicate Event ID detected: '{spec.event_id}'. Event IDs must be unique.")
            else:
                seen_events.add(spec.event_id)

        # 2. Check Process IDs
        for spec in self.event_specs:
            if spec.process_id not in self.process_ids:
                errors.append(f"Event '{spec.event_id}' belongs to unknown process '{spec.process_id}'. Configured: {self.process_ids}")

        # 3. Message validation
        # Map message_id -> send_event_spec, index
        sent_messages: Dict[str, Tuple[EventSpec, int]] = {}
        # Track duplicate sends
        for idx, spec in enumerate(self.event_specs):
            if spec.event_type == EventType.SEND:
                if not spec.message_id or spec.message_id.strip() == "":
                    errors.append(f"Send event '{spec.event_id}' has no Message ID specified.")
                elif spec.message_id in sent_messages:
                    errors.append(f"Duplicate Send Message ID: '{spec.message_id}' is sent more than once.")
                else:
                    sent_messages[spec.message_id] = (spec, idx)

                if not spec.target_process:
                    errors.append(f"Send event '{spec.event_id}' must specify a target process.")
                elif spec.target_process not in self.process_ids:
                    errors.append(f"Send event '{spec.event_id}' targets unknown process '{spec.target_process}'.")
                elif spec.target_process == spec.process_id:
                    errors.append(f"Send event '{spec.event_id}' has source and target as the same process '{spec.process_id}'.")

        # Check receives
        received_messages: Set[str] = set()
        for idx, spec in enumerate(self.event_specs):
            if spec.event_type == EventType.RECEIVE:
                if not spec.message_id or spec.message_id.strip() == "":
                    errors.append(f"Receive event '{spec.event_id}' has no Message ID specified.")
                    continue

                if spec.message_id in received_messages:
                    errors.append(f"Duplicate Receive: Message '{spec.message_id}' is received multiple times.")
                received_messages.add(spec.message_id)

                if spec.message_id not in sent_messages:
                    errors.append(
                        f"Receive event '{spec.event_id}' attempts to receive message '{spec.message_id}' "
                        f"which was never sent!"
                    )
                else:
                    send_spec, send_idx = sent_messages[spec.message_id]
                    # Check causality: receive must appear after send in execution sequence
                    if idx <= send_idx:
                        errors.append(
                            f"Causality Violation: Receive event '{spec.event_id}' occurs at step #{idx + 1} "
                            f"BEFORE message '{spec.message_id}' is sent at step #{send_idx + 1}."
                        )

                    # Check process matching
                    if send_spec.target_process != spec.process_id:
                        errors.append(
                            f"Process Mismatch: Message '{spec.message_id}' was addressed to '{send_spec.target_process}', "
                            f"but '{spec.process_id}' attempts to receive it."
                        )
                    if spec.source_process and spec.source_process != send_spec.process_id:
                        errors.append(
                            f"Source Mismatch: Receive event '{spec.event_id}' expects sender '{spec.source_process}', "
                            f"but '{send_spec.process_id}' sent message '{spec.message_id}'."
                        )

        # Check for unreceived messages (warning only)
        for msg_id, (send_spec, _) in sent_messages.items():
            if msg_id not in received_messages:
                warnings.append(
                    f"Message '{msg_id}' sent by '{send_spec.process_id}' to '{send_spec.target_process}' "
                    f"is in-flight (not yet received in this schedule)."
                )

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    def run(self) -> SimulationResult:
        """
        Execute the simulation dynamically according to Lamport Logical Clock rules.
        """
        is_valid, errors, _ = self.validate()
        if not is_valid:
            raise ValueError("Cannot run simulation with invalid event specification:\n" + "\n".join(errors))

        # Initialize processes
        processes: Dict[str, LamportProcess] = {
            pid: LamportProcess(pid) for pid in self.process_ids
        }
        messages: Dict[str, Message] = {}
        executed_events: List[Event] = []
        step_snapshots: List[Dict] = []

        # Sequential dynamic execution
        for step_idx, spec in enumerate(self.event_specs, start=1):
            proc = processes[spec.process_id]
            event: Event

            if spec.event_type == EventType.INTERNAL:
                event = proc.execute_internal(spec.event_id, spec.custom_desc)

            elif spec.event_type == EventType.SEND:
                event, msg = proc.execute_send(
                    spec.event_id,
                    spec.message_id,  # type: ignore
                    spec.target_process,  # type: ignore
                    spec.custom_desc
                )
                messages[spec.message_id] = msg  # type: ignore

            elif spec.event_type == EventType.RECEIVE:
                msg = messages[spec.message_id]  # type: ignore
                event = proc.execute_receive(spec.event_id, msg, spec.custom_desc)

            else:
                raise ValueError(f"Unknown event type: {spec.event_type}")

            event.step_number = step_idx
            executed_events.append(event)

            # Record snapshot after this step
            step_snapshots.append({
                "step": step_idx,
                "current_event": event,
                "clocks": {pid: p.clock for pid, p in processes.items()},
                "history_so_far": list(executed_events)
            })

        # Process-wise events
        process_events: Dict[str, List[Event]] = defaultdict(list)
        for ev in executed_events:
            process_events[ev.process_id].append(ev)

        # Lamport Total Ordering:
        # Sort key: (Lamport Clock, Process ID numeric/lexicographic, Event ID)
        total_order = sorted(
            executed_events,
            key=lambda e: (e.clock, e.process_id, e.event_id)
        )

        # Compute causality (happens-before relation)
        causality_matrix = self._compute_happens_before(executed_events, messages)

        return SimulationResult(
            events=executed_events,
            messages=messages,
            process_clocks={pid: p.clock for pid, p in processes.items()},
            process_events=dict(process_events),
            total_order=total_order,
            causality_matrix=causality_matrix,
            step_snapshots=step_snapshots
        )

    def _compute_happens_before(self, events: List[Event], messages: Dict[str, Message]) -> Dict[Tuple[str, str], str]:
        """
        Compute the Happens-Before relation (->) for all event pairs using Reachability in the DAG.
        
        Rules:
        1. If a and b are in the same process and a executed before b, then a -> b.
        2. If a is the sending of message m and b is the receipt of m, then a -> b.
        3. If a -> b and b -> c, then a -> c (transitivity).
        4. If neither a -> b nor b -> a, then a || b (concurrent).
        """
        event_ids = [e.event_id for e in events]
        n = len(event_ids)
        event_map = {e.event_id: e for e in events}

        # Build adjacency graph for direct causality edges
        adj = defaultdict(set)

        # 1. Intra-process sequential edges
        proc_events: Dict[str, List[Event]] = defaultdict(list)
        for e in events:
            proc_events[e.process_id].append(e)

        for p_evs in proc_events.values():
            for i in range(len(p_evs) - 1):
                adj[p_evs[i].event_id].add(p_evs[i + 1].event_id)

        # 2. Message send -> receive edges
        # Map message_id to (send_event_id, receive_event_id)
        send_map: Dict[str, str] = {}
        for e in events:
            if e.event_type == EventType.SEND and e.message_id:
                send_map[e.message_id] = e.event_id

        for e in events:
            if e.event_type == EventType.RECEIVE and e.message_id:
                sender_event_id = send_map.get(e.message_id)
                if sender_event_id:
                    adj[sender_event_id].add(e.event_id)

        # 3. Transitive closure (Reachability matrix)
        reach = {eid1: {eid2: False for eid2 in event_ids} for eid1 in event_ids}
        for u in event_ids:
            reach[u][u] = True
            for v in adj[u]:
                reach[u][v] = True

        for k in event_ids:
            for i in event_ids:
                for j in event_ids:
                    if reach[i][k] and reach[k][j]:
                        reach[i][j] = True

        # 4. Construct causality matrix
        result: Dict[Tuple[str, str], str] = {}
        for i in range(n):
            for j in range(n):
                id_a = event_ids[i]
                id_b = event_ids[j]
                if id_a == id_b:
                    result[(id_a, id_b)] = "Same Event"
                elif reach[id_a][id_b]:
                    result[(id_a, id_b)] = f"{id_a} -> {id_b} (Happened Before)"
                elif reach[id_b][id_a]:
                    result[(id_a, id_b)] = f"{id_b} -> {id_a} (Happened After)"
                else:
                    result[(id_a, id_b)] = f"{id_a} || {id_b} (Concurrent)"

        return result

    # -------------------------------------------------------------
    # PRESET CONFIGURATIONS FOR QUICK VIVA / LAB DEMONSTRATION
    # -------------------------------------------------------------

    @classmethod
    def load_preset_1_college_demo(cls) -> "SimulationEngine":
        """
        Preset 1: The standard college viva demonstration example from the prompt.
        P1:
          E1 = Internal
          E2 = Send M1 to P2
        P2:
          E3 = Internal
          E4 = Receive M1 from P1
        P3:
          E5 = Internal
          E6 = Send M2 to P1
        P1:
          E7 = Receive M2 from P3
        """
        sim = cls(process_ids=["P1", "P2", "P3"])
        sim.add_event(EventSpec(event_id="E1", process_id="P1", event_type=EventType.INTERNAL, custom_desc="P1 performs internal calculation"))
        sim.add_event(EventSpec(event_id="E2", process_id="P1", event_type=EventType.SEND, message_id="M1", target_process="P2", custom_desc="P1 sends message M1 to P2"))
        sim.add_event(EventSpec(event_id="E3", process_id="P2", event_type=EventType.INTERNAL, custom_desc="P2 performs local database read"))
        sim.add_event(EventSpec(event_id="E4", process_id="P2", event_type=EventType.RECEIVE, message_id="M1", source_process="P1", custom_desc="P2 receives message M1 from P1"))
        sim.add_event(EventSpec(event_id="E5", process_id="P3", event_type=EventType.INTERNAL, custom_desc="P3 performs background logging"))
        sim.add_event(EventSpec(event_id="E6", process_id="P3", event_type=EventType.SEND, message_id="M2", target_process="P1", custom_desc="P3 sends message M2 to P1"))
        sim.add_event(EventSpec(event_id="E7", process_id="P1", event_type=EventType.RECEIVE, message_id="M2", source_process="P3", custom_desc="P1 receives message M2 from P3"))
        return sim

    @classmethod
    def load_preset_2_four_processes_cascade(cls) -> "SimulationEngine":
        """
        Preset 2: 4-process pipeline demonstrating transitive clock progression.
        P1 -> P2 -> P3 -> P4
        """
        sim = cls(process_ids=["P1", "P2", "P3", "P4"])
        sim.add_event(EventSpec(event_id="E1", process_id="P1", event_type=EventType.INTERNAL, custom_desc="P1 initialization"))
        sim.add_event(EventSpec(event_id="E2", process_id="P1", event_type=EventType.SEND, message_id="M1", target_process="P2", custom_desc="P1 forwards packet to P2"))
        sim.add_event(EventSpec(event_id="E3", process_id="P2", event_type=EventType.RECEIVE, message_id="M1", source_process="P1", custom_desc="P2 receives packet from P1"))
        sim.add_event(EventSpec(event_id="E4", process_id="P2", event_type=EventType.SEND, message_id="M2", target_process="P3", custom_desc="P2 relays data to P3"))
        sim.add_event(EventSpec(event_id="E5", process_id="P3", event_type=EventType.RECEIVE, message_id="M2", source_process="P2", custom_desc="P3 receives data from P2"))
        sim.add_event(EventSpec(event_id="E6", process_id="P3", event_type=EventType.SEND, message_id="M3", target_process="P4", custom_desc="P3 transmits payload to P4"))
        sim.add_event(EventSpec(event_id="E7", process_id="P4", event_type=EventType.RECEIVE, message_id="M3", source_process="P3", custom_desc="P4 receives final payload"))
        sim.add_event(EventSpec(event_id="E8", process_id="P4", event_type=EventType.INTERNAL, custom_desc="P4 completes transaction"))
        return sim

    @classmethod
    def load_preset_3_concurrency_clock_jump(cls) -> "SimulationEngine":
        """
        Preset 3: Concurrency and significant clock jump demonstration.
        P1 runs ahead with 3 internal events (clocks 1, 2, 3), sends M1 (clock 4).
        P2 is idle at clock 0, then receives M1 -> clock jumps straight from 0 to max(0, 4) + 1 = 5!
        """
        sim = cls(process_ids=["P1", "P2", "P3"])
        sim.add_event(EventSpec(event_id="E1", process_id="P1", event_type=EventType.INTERNAL, custom_desc="P1 quick compute step 1"))
        sim.add_event(EventSpec(event_id="E2", process_id="P1", event_type=EventType.INTERNAL, custom_desc="P1 quick compute step 2"))
        sim.add_event(EventSpec(event_id="E3", process_id="P1", event_type=EventType.INTERNAL, custom_desc="P1 quick compute step 3"))
        sim.add_event(EventSpec(event_id="E4", process_id="P3", event_type=EventType.INTERNAL, custom_desc="P3 independent task (Concurrent with E1/E2/E3)"))
        sim.add_event(EventSpec(event_id="E5", process_id="P1", event_type=EventType.SEND, message_id="M1", target_process="P2", custom_desc="P1 sends M1 with Tm=4 to slow process P2"))
        sim.add_event(EventSpec(event_id="E6", process_id="P2", event_type=EventType.RECEIVE, message_id="M1", source_process="P1", custom_desc="P2 clock leaps from 0 to max(0, 4) + 1 = 5!"))
        sim.add_event(EventSpec(event_id="E7", process_id="P2", event_type=EventType.SEND, message_id="M2", target_process="P3", custom_desc="P2 sends M2 to P3"))
        sim.add_event(EventSpec(event_id="E8", process_id="P3", event_type=EventType.RECEIVE, message_id="M2", source_process="P2", custom_desc="P3 syncs with P2"))
        return sim
