"""
lamport_clock.py
================
Core implementation of Lamport's Logical Clock algorithm.
Designed for educational clarity and college viva demonstration.

Rules of Lamport Logical Clocks:
--------------------------------
1. Initialization:
   Every process Pi initializes its local clock to 0: Ci = 0

2. Rule 1 (Internal Event):
   Before executing an internal event, the process increments its clock:
   Ci = Ci + 1

3. Rule 2 (Send Event):
   Before sending a message m, the process increments its clock:
   Ci = Ci + 1
   The message carries the timestamp: Tm = Ci

4. Rule 3 (Receive Event):
   Upon receiving a message m with timestamp Tm, the process updates its clock:
   Cj = max(Cj, Tm) + 1

5. Total Ordering (Tie-Breaking):
   For two events a and b:
   a < b iff (Ci(a) < Cj(b)) OR (Ci(a) == Cj(b) AND Pi < Pj)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class EventType(str, Enum):
    """Enumeration of possible event types in a distributed system."""
    INTERNAL = "Internal"
    SEND = "Send"
    RECEIVE = "Receive"


@dataclass
class Event:
    """Represents a single event in the distributed system."""
    event_id: str
    process_id: str
    event_type: EventType
    prev_clock: int = 0
    received_timestamp: Optional[int] = None
    clock: int = 0
    message_id: Optional[str] = None
    target_process: Optional[str] = None
    source_process: Optional[str] = None
    description: str = ""
    step_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for DataFrame rendering."""
        return {
            "Step": self.step_number,
            "Event ID": self.event_id,
            "Process": self.process_id,
            "Event Type": self.event_type.value if isinstance(self.event_type, EventType) else str(self.event_type),
            "Prev Clock": self.prev_clock,
            "Received Timestamp (Tm)": self.received_timestamp if self.received_timestamp is not None else "-",
            "New Clock (C)": self.clock,
            "Description": self.description
        }


@dataclass
class Message:
    """Represents a message sent between processes."""
    message_id: str
    source_process: str
    target_process: str
    sent_timestamp: int
    is_delivered: bool = False
    delivery_clock: Optional[int] = None


class LamportProcess:
    """
    Represents an individual logical process in a distributed system.
    Maintains its own integer logical clock according to Lamport's algorithm.
    """

    def __init__(self, process_id: str):
        self.process_id = process_id
        self.clock: int = 0
        self.history: list[Event] = []

    def reset(self) -> None:
        """Reset the process clock and history."""
        self.clock = 0
        self.history.clear()

    def execute_internal(self, event_id: str, description: str = "") -> Event:
        """
        Execute an internal event (Rule 1):
        C = C + 1
        """
        prev = self.clock
        self.clock += 1
        desc = description or f"Internal event executed: C = {prev} + 1 = {self.clock}"
        event = Event(
            event_id=event_id,
            process_id=self.process_id,
            event_type=EventType.INTERNAL,
            prev_clock=prev,
            clock=self.clock,
            description=desc
        )
        self.history.append(event)
        return event

    def execute_send(self, event_id: str, message_id: str, target_process: str, description: str = "") -> tuple[Event, Message]:
        """
        Execute a send event (Rule 2):
        C = C + 1
        Attach timestamp Tm = C to the message.
        """
        prev = self.clock
        self.clock += 1
        timestamp = self.clock
        desc = description or f"Sent message {message_id} to {target_process}: C = {prev} + 1 = {self.clock} (Tm={timestamp})"
        event = Event(
            event_id=event_id,
            process_id=self.process_id,
            event_type=EventType.SEND,
            prev_clock=prev,
            clock=self.clock,
            message_id=message_id,
            target_process=target_process,
            description=desc
        )
        message = Message(
            message_id=message_id,
            source_process=self.process_id,
            target_process=target_process,
            sent_timestamp=timestamp
        )
        self.history.append(event)
        return event, message

    def execute_receive(self, event_id: str, message: Message, description: str = "") -> Event:
        """
        Execute a receive event (Rule 3):
        C = max(C, Tm) + 1
        """
        prev = self.clock
        tm = message.sent_timestamp
        self.clock = max(prev, tm) + 1
        message.is_delivered = True
        message.delivery_clock = self.clock

        desc = description or (
            f"Received message {message.message_id} from {message.source_process} with Tm={tm}: "
            f"C = max({prev}, {tm}) + 1 = {self.clock}"
        )
        event = Event(
            event_id=event_id,
            process_id=self.process_id,
            event_type=EventType.RECEIVE,
            prev_clock=prev,
            received_timestamp=tm,
            clock=self.clock,
            message_id=message.message_id,
            source_process=message.source_process,
            description=desc
        )
        self.history.append(event)
        return event
