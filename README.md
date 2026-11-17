# ⏱️ Lamport Logical Clock Simulator

> **Distributed Computing Mini Project**  
> An interactive educational simulator demonstrating logical time synchronization, happens-before causality ($\to$), and total event ordering across distributed processes using **Lamport's Logical Clock Algorithm**.

---

## 📋 Table of Contents
1. [Project Title](#1-project-title)
2. [Problem Statement](#2-problem-statement)
3. [Project Objective](#3-project-objective)
4. [Introduction](#4-introduction)
5. [Lamport Logical Clock Concept](#5-lamport-logical-clock-concept)
6. [Algorithm Rules & Mathematical Foundation](#6-algorithm-rules--mathematical-foundation)
7. [System Architecture](#7-system-architecture)
8. [Technologies Used](#8-technologies-used)
9. [How the Simulator Works](#9-how-the-simulator-works)
10. [Sample Input](#10-sample-input)
11. [Sample Output](#11-sample-output)
12. [Installation Steps](#12-installation-steps)
13. [How to Run](#13-how-to-run)
14. [Expected Result](#14-expected-result)
15. [Advantages](#15-advantages)
16. [Limitations](#16-limitations)
17. [Future Enhancements](#17-future-enhancements)
18. [System Architecture & Flowchart Diagrams](#18-system-architecture--flowchart-diagrams)
19. [Sample Test Cases & Verification](#19-sample-test-cases--verification)
20. [🎓 College Viva Preparation Guide (17 Q&A)](#20--college-viva-preparation-guide-17-qa)

---

## 1. Project Title
**Lamport Logical Clock Simulator for Distributed Systems**

---

## 2. Problem Statement
In a distributed computing system, multiple autonomous processes run on independent machines across a computer network without shared memory or a single synchronized physical clock. Due to physical factors like crystal oscillator frequency variations, ambient temperature fluctuations, and non-deterministic network transmission delays:
- Physical clocks inevitably experience **clock drift** and **clock skew**.
- Determining the exact chronological or causal order of distributed events (e.g., whether transaction $A$ happened before transaction $B$) using physical timestamps is fundamentally unreliable and leads to race conditions, inconsistent replicas, and synchronization anomalies.

Hence, a software-level logical mechanism is required to establish consistent ordering of events based on causality rather than physical time.

---

## 3. Project Objective
- **Demonstrate Causality:** Simulate multiple distributed processes (3 to 4 nodes) maintaining independent logical clocks.
- **Implement Lamport's Rules:** Calculate dynamic clock updates for **Internal**, **Send**, and **Receive** events following Leslie Lamport's 1978 seminal specification.
- **Visualize Space-Time Interaction:** Render interactive space-time process baselines and message transmission vectors.
- **Derive Event Orderings:** Demonstrate both **Partial Ordering** (Happens-Before relation $\to$) and **Total Ordering** (tie-breaking via Process ID).
- **Interactive Step-by-Step Execution:** Provide an intuitive tool suitable for college lab presentations, project evaluation, and oral viva defense.

---

## 4. Introduction
Leslie Lamport introduced logical clocks in his 1978 paper *"Time, Clocks, and the Ordering of Events in a Distributed System"*, which remains one of the most cited works in computer science. Lamport recognized that what matters in distributed algorithms is not absolute wall-clock time, but rather **causality**: whether event $A$ could have influenced or caused event $B$.

This project provides a clean, self-contained desktop simulator written in Python and Streamlit. It allows students, educators, and examiners to create, step through, and analyze distributed event traces without requiring complex network setup or cloud infrastructure.

---

## 5. Lamport Logical Clock Concept

### 5.1 The Happens-Before Relation ($\to$)
The relation "$\to$" defines causal precedence between events:
1. **Intra-Process Order:** If events $a$ and $b$ occur within the same process $P_i$, and $a$ occurs before $b$, then $a \to b$.
2. **Inter-Process Message Passing:** If $a$ is the sending of a message $m$ by process $P_i$, and $b$ is the receipt of that same message by process $P_j$, then $a \to b$.
3. **Transitivity:** If $a \to b$ and $b \to c$, then $a \to c$.
4. **Concurrency ($\parallel$):** If neither $a \to b$ nor $b \to a$ holds, the two events are **concurrent** ($a \parallel b$).

### 5.2 The Clock Condition
For any events $a$ and $b$:
$$\text{If } a \to b \implies C(a) < C(b)$$

> **CRITICAL VIVA POINT:** The reverse is **NOT** necessarily true! If $C(a) < C(b)$, event $a$ did not necessarily happen before $b$; they could be concurrent ($a \parallel b$).

---

## 6. Algorithm Rules & Mathematical Foundation

Each process $P_i$ maintains an integer counter $C_i$, initialized to $0$:

### Rule 1: Internal Event
Before executing an internal event:
$$C_i = C_i + 1$$

### Rule 2: Send Message Event
Before sending message $m$, process $P_i$ increments its clock and attaches the timestamp $T_m$:
$$C_i = C_i + 1$$
$$T_m = C_i$$

### Rule 3: Receive Message Event
Upon receiving message $m$ containing timestamp $T_m$, process $P_j$ updates its clock:
$$C_j = \max(C_j, T_m) + 1$$

### Rule 4: Total Ordering (Tie-Breaking)
To construct a strict total order ($\Rightarrow$) across all distributed events:
$$a \Rightarrow b \iff (C(a) < C(b)) \lor (C(a) = C(b) \land \text{Process\_ID}(a) < \text{Process\_ID}(b))$$

---

## 7. System Architecture

The project strictly decouples core mathematical logic from visualization:

```
┌────────────────────────────────────────────────────────┐
│                   STREAMLIT WEB UI                     │
│  (app.py - Dashboards, Plotly Space-Time, Sliders)     │
└───────────────────────────┬────────────────────────────┘
                            │ User Input / Presets
                            ▼
┌────────────────────────────────────────────────────────┐
│                  SIMULATION ENGINE                     │
│  (simulator.py - Validation, DAG, Transitive Closure)   │
└───────────────────────────┬────────────────────────────┘
                            │ Execute Clock Rules
                            ▼
┌────────────────────────────────────────────────────────┐
│                 LAMPORT CLOCK CORE                     │
│  (lamport_clock.py - Process, Event, Message Classes)  │
│      Ci = Ci + 1    |    Cj = max(Cj, Tm) + 1          │
└────────────────────────────────────────────────────────┘
```

---

## 8. Technologies Used
- **Python 3.10+ / 3.13:** Core programming language.
- **Streamlit:** Fast, clean, reactive web dashboard.
- **Plotly:** Interactive space-time timeline diagram with message vectors.
- **Pandas:** Tabular presentation of execution logs and causality matrices.
- **Pytest:** Automated test verification framework.
- **No External Database:** 100% locally self-contained in memory.
- **No API Keys or Cloud Dependencies:** Zero setup friction.

---

## 9. How the Simulator Works
1. **Process Configuration:** The user selects 3 or 4 processes ($P_1, P_2, P_3, P_4$).
2. **Event Definition:** Events are defined with type (`Internal`, `Send`, `Receive`), source, and destination.
3. **Validation Stage:** Before calculation, the engine validates:
   - Unique Event IDs
   - Valid sender and receiver processes
   - No delivery of un-sent messages
   - Causality checks (no message received before it is sent)
4. **Dynamic Execution:** Iterates through events in sequence, dynamically updating local process clocks using Lamport rules.
5. **Causality & Ordering Analysis:**
   - Computes transitive reachability across the Directed Acyclic Graph (DAG) to classify pairs as $\to$, $\leftarrow$, or $\parallel$.
   - Generates the tie-broken total order table.
6. **Rendering:** Draws the space-time diagram, message cards, and event table.

---

## 10. Sample Input

### Preset 1: College Demo Example
```text
Processes: P1, P2, P3

Event Sequence:
1. P1: E1 = Internal
2. P1: E2 = Send message M1 to P2
3. P2: E3 = Internal
4. P2: E4 = Receive message M1 from P1
5. P3: E5 = Internal
6. P3: E6 = Send message M2 to P1
7. P1: E7 = Receive message M2 from P3
```

---

## 11. Sample Output

### Event Table
| Step | Event ID | Process | Event Type | Prev Clock | Received $T_m$ | New Clock ($C$) | Applied Rule / Description |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | **E1** | P1 | Internal | 0 | - | **1** | $C = 0 + 1 = 1$ |
| 2 | **E2** | P1 | Send | 1 | - | **2** | $C = 1 + 1 = 2$, sent $M1$ with $T_m=2$ |
| 3 | **E3** | P2 | Internal | 0 | - | **1** | $C = 0 + 1 = 1$ |
| 4 | **E4** | P2 | Receive | 1 | 2 | **3** | $C = \max(1, 2) + 1 = 3$ |
| 5 | **E5** | P3 | Internal | 0 | - | **1** | $C = 0 + 1 = 1$ |
| 6 | **E6** | P3 | Send | 1 | - | **2** | $C = 1 + 1 = 2$, sent $M2$ with $T_m=2$ |
| 7 | **E7** | P1 | Receive | 2 | 2 | **3** | $C = \max(2, 2) + 1 = 3$ |

### Lamport Total Ordering Result ($a \Rightarrow b$)
```text
Rank 1: E1 (P1, Clock=1)
Rank 2: E3 (P2, Clock=1)   <-- Tie-break: P1 < P2 < P3
Rank 3: E5 (P3, Clock=1)
Rank 4: E2 (P1, Clock=2)
Rank 5: E6 (P3, Clock=2)   <-- Tie-break: P1 < P3
Rank 6: E7 (P1, Clock=3)
Rank 7: E4 (P2, Clock=3)   <-- Tie-break: P1 < P2
```

---

## 12. Installation Steps

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.

### Step-by-Step Setup
1. Clone or copy the project folder to your local machine:
   ```bash
   cd c:\Users\ACER\Desktop\DC
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 13. How to Run

### Method 1: Using the Command Line
```bash
python -m streamlit run app.py
```

### Method 2: One-Click Launch on Windows
Double-click `run.bat` located inside the project directory.

The browser will open at:
```
Local URL: http://localhost:8501
```

---

## 14. Expected Result
- The dashboard launches with **Preset 1 (College Demo)** loaded by default.
- You will see:
  1. Top KPI summary cards and algorithm rule cheat sheet.
  2. Interactive Plotly Space-Time timeline showing $P1$, $P2$, and $P3$ with colored event nodes and directed purple arrows for messages $M1$ and $M2$.
  3. Dynamic calculation table with exact formula breakdown.
  4. Step-by-step playback slider enabling single-step forward/backward tracing.
  5. Total order table and pairwise causality checker.

---

## 15. Advantages
- **No Physical Clock Dependency:** Solves event ordering purely via software message counters.
- **Deterministic Total Order:** Well-defined tie-breaking ensures all distributed nodes can agree on event order.
- **Lightweight & Fast:** Minimal overhead; integer increments take $O(1)$ time.
- **Educational Value:** Clear visual space-time diagram makes abstract concepts concrete.

---

## 16. Limitations
- **Inability to Detect Concurrency from Clocks Alone:** $C(a) < C(b)$ does **not** imply $a \to b$. Two events could have different clock values while being causally independent.
- **Vector Clocks Needed for Strong Causality:** To guarantee $a \to b \iff C(a) < C(b)$, vector clocks are required.
- **Unbounded Counter Growth:** In long-running distributed applications, integer clock values grow indefinitely.
- **Arbitrary Total Ordering:** Breaking ties by Process ID is an arbitrary convention and does not reflect actual physical time precedence.

---

## 17. Future Enhancements
- **Vector Clock Extension:** Add an interactive side-by-side comparison between Lamport Clocks and Vector Clocks ($V_i[j]$).
- **Network Latency Simulation:** Introduce configurable random delay and out-of-order message delivery channels.
- **Distributed Mutual Exclusion:** Implement Lamport's Distributed Mutual Exclusion algorithm or Ricart-Agrawala algorithm on top of the clock engine.

---

## 18. System Architecture & Flowchart Diagrams

### 18.1 Lamport Logical Clock Algorithm Flowchart
```
                ┌──────────────────────────────────┐
                │   Event e occurs at Process Pi   │
                └─────────────────┬────────────────┘
                                  │
                                  ▼
                     /─────────────────────────\
                    <   What is the Event Type? >
                     \─────────────────────────/
                       /          │          \
           Internal   /      Send │           \ Receive with Tm
                     ▼            ▼            ▼
             ┌────────────┐┌────────────┐┌──────────────────────┐
             │ Ci = Ci + 1││ Ci = Ci + 1││ Ci = max(Ci, Tm) + 1 │
             └─────┬──────┘│ Tm = Ci    │└──────────┬───────────┘
                   │       │ Attach Tm  │           │
                   │       └─────┬──────┘           │
                   │             │                  │
                   └───────────┐ │ ┌────────────────┘
                               ▼ ▼ ▼
                ┌──────────────────────────────────┐
                │  Record Event in Local History   │
                │  Update Space-Time Visualization │
                └─────────────────┬────────────────┘
                                  │
                                  ▼
                ┌──────────────────────────────────┐
                │  Compute Total Order & Causality │
                └──────────────────────────────────┘
```

### 18.2 System Architecture Diagram
```
                     +----------------------------+
                     |    User / Examiner         |
                     +--------------+-------------+
                                    |
                                    v
                     +----------------------------+
                     |  Streamlit UI (app.py)     |
                     |  - Process Select (3 or 4) |
                     |  - Event Builder Form      |
                     |  - Step Playback Slider    |
                     |  - Space-Time Plotly Chart |
                     +--------------+-------------+
                                    |
                    Event Specs     | Validated Results
                                    v
                     +----------------------------+
                     | Simulator Engine           |
                     | (simulator.py)             |
                     |  - Validation Logic        |
                     |  - DAG Reachability Engine |
                     |  - Total Order Sorter      |
                     +--------------+-------------+
                                    |
                    Executes Rules  | Returns Clocks
                                    v
                     +----------------------------+
                     | Lamport Clock Core         |
                     | (lamport_clock.py)         |
                     |  - LamportProcess          |
                     |  - Event & Message Model   |
                     |  - Rule 1, Rule 2, Rule 3  |
                     +----------------------------+
```

---

## 19. Sample Test Cases & Verification

### Test Case 1: Standard Preset (Prompt Demo)
- **Input:** 3 Processes ($P1, P2, P3$), 7 events with messages $M1$ ($P1 \to P2$) and $M2$ ($P3 \to P1$).
- **Expected Clocks:**
  - $E1 (P1): 1$
  - $E2 (P1, \text{send } M1): 2$
  - $E3 (P2): 1$
  - $E4 (P2, \text{recv } M1): 3$ (formula: $\max(1, 2) + 1 = 3$)
  - $E5 (P3): 1$
  - $E6 (P3, \text{send } M2): 2$
  - $E7 (P1, \text{recv } M2): 3$ (formula: $\max(2, 2) + 1 = 3$)
- **Automated Test:** `test_preset_1_college_demo` in `test_simulator.py` -> **PASSED**.

### Test Case 2: 4-Process Pipeline
- **Input:** 4 Processes ($P1, P2, P3, P4$), cascade $P1 \to P2 \to P3 \to P4$.
- **Expected Clocks:** $E1:1, E2:2, E3:3, E4:4, E5:5, E6:6, E7:7, E8:8$.
- **Automated Test:** `test_preset_2_pipeline` in `test_simulator.py` -> **PASSED**.

### Test Case 3: Invalid Sequence (Receive Before Send)
- **Input:** $P2$ receives $M1$ before $P1$ sends $M1$.
- **Expected Behavior:** Simulator intercepts error and reports *"Causality Violation"*.
- **Automated Test:** `test_validation_errors` in `test_simulator.py` -> **PASSED**.

---

## 20. 🎓 College Viva Preparation Guide (17 Q&A)

### Q1: What is a Distributed System?
**Answer:** A distributed system consists of multiple autonomous computing entities that communicate over a network by message passing. It lacks shared memory and a shared global physical clock, coordinating actions solely via network messages.

### Q2: Why can't distributed systems use physical clocks for event ordering?
**Answer:** Physical clocks (quartz crystals) suffer from clock drift and skew caused by temperature, voltage fluctuations, and hardware manufacturing differences. Network latency is non-deterministic, making absolute physical clock synchronization impossible without specialized atomic hardware (e.g., Google Spanner's TrueTime).

### Q3: What is a Logical Clock?
**Answer:** A logical clock is a monotonically increasing software counter maintained locally by each process to capture the causal ordering of events without referencing physical wall-clock time.

### Q4: Define the Happens-Before Relation ($\to$).
**Answer:** Introduced by Leslie Lamport in 1978:
1. If $a$ and $b$ are in the same process and $a$ occurs before $b$, then $a \to b$.
2. If $a$ is sending a message and $b$ is receiving that message, then $a \to b$.
3. If $a \to b$ and $b \to c$, then $a \to c$ (transitivity).

### Q5: State the three rules of Lamport's Logical Clock algorithm.
**Answer:**
- **Internal Event:** $C_i = C_i + 1$
- **Send Event:** $C_i = C_i + 1$, attach $T_m = C_i$ to message $m$.
- **Receive Event:** When $P_j$ receives $m$ with timestamp $T_m$, it computes: $C_j = \max(C_j, T_m) + 1$.

### Q6: Why is the "+ 1" added in the receive rule $C_j = \max(C_j, T_m) + 1$?
**Answer:** Because message transmission requires non-zero time, the receipt event must strictly succeed the send event in logical time. Adding $+1$ guarantees that $C(\text{receive}) > C(\text{send})$.

### Q7: What is the Clock Condition?
**Answer:** For any two events $a$ and $b$:
$$\text{If } a \to b \implies C(a) < C(b)$$
Lamport's algorithm strictly satisfies this condition.

### Q8: Does $C(a) < C(b)$ imply that $a \to b$?
**Answer:** **No!** Lamport clocks only guarantee the forward implication. If $C(a) < C(b)$, event $a$ could have happened before $b$, or $a$ and $b$ could be **concurrent** ($a \parallel b$). Lamport clocks cannot detect causality backwards.

### Q9: How does a Vector Clock improve upon Lamport's Clock?
**Answer:** A Vector Clock maintains an integer vector of size $N$ (number of processes). Vector clocks guarantee a two-way equivalence:
$$V(a) < V(b) \iff a \to b$$
This allows distributed systems to detect concurrency precisely.

### Q10: How does Lamport define a Total Order on events?
**Answer:** Lamport creates a strict total order ($\Rightarrow$) by breaking ties using unique process identifiers:
$$a \Rightarrow b \iff (C(a) < C(b)) \lor (C(a) = C(b) \land P_a < P_b)$$

### Q11: Why is Total Ordering useful in distributed systems?
**Answer:** Total ordering is essential for distributed mutual exclusion (ensuring only one process enters a critical section) and state machine replication (ensuring every database replica applies mutations in the exact same order).

### Q12: What does it mean for two events to be concurrent ($a \parallel b$)?
**Answer:** Events $a$ and $b$ are concurrent if neither event causally affected the other ($a \not\to b$ and $b \not\to a$). Neither process had knowledge of the other event when executing.

### Q13: What is a Causality Violation?
**Answer:** A causality violation occurs when an effect is observed before its cause—for instance, receiving a message before it has been sent, or receiving a response before the request.

### Q14: Differentiate between Clock Drift and Clock Skew.
**Answer:**
- **Clock Skew:** The instantaneous difference in reading between two clocks at a given moment.
- **Clock Drift:** The rate at which clock skew changes over time due to differences in oscillator frequencies.

### Q15: What are the main limitations of Lamport Clocks?
**Answer:**
1. Cannot detect concurrency ($C(a) < C(b) \not\implies a \to b$).
2. Total order tie-breaking is arbitrary (based on process IDs, not real time).
3. Integer clock values grow unboundedly over long periods.
4. Cannot measure actual elapsed physical duration.

### Q16: How does this simulator validate event sequences?
**Answer:** It checks for:
- Non-existent process IDs.
- Duplicate event or message identifiers.
- Receiving messages that were never sent.
- Receiving messages before their send events (causality violations).
- Sending messages to oneself or mismatched target processes.

### Q17: What was Leslie Lamport's key insight in his 1978 paper?
**Answer:** Lamport realized that absolute physical time is unnecessary for distributed coordination; what matters is the partial order of events determined by message passing and causality.
