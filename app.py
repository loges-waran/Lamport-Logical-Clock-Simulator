"""
app.py
======
Lamport Logical Clock Simulator
Distributed Computing Mini Project

Interactive Streamlit Web Application demonstrating:
- Lamport's Logical Clock Rules (Internal, Send, Receive)
- Dynamic Clock Calculation
- Process Space-Time Timeline & Message Arrows
- Total Ordering & Happens-Before Causality Analysis
- Step-by-Step Simulation Playback
- Preset College Viva Scenarios & Interactive Event Builder
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict

from lamport_clock import EventType, Event, Message
from simulator import SimulationEngine, EventSpec, SimulationResult


# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Lamport Logical Clock Simulator",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished college project aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .rule-card {
        background-color: #F8FAFC;
        border-left: 4px solid #3B82F6;
        padding: 0.8rem 1.2rem;
        border-radius: 4px;
        margin-bottom: 0.8rem;
        font-size: 0.92rem;
    }
    .badge-internal {
        background-color: #0284C7;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-send {
        background-color: #EA580C;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-receive {
        background-color: #16A34A;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "num_processes" not in st.session_state:
    st.session_state.num_processes = 3

if "processes" not in st.session_state:
    st.session_state.processes = ["P1", "P2", "P3"]

if "event_specs" not in st.session_state:
    # Load College Demo Preset by default
    default_engine = SimulationEngine.load_preset_1_college_demo()
    st.session_state.event_specs = default_engine.event_specs

if "step_index" not in st.session_state:
    st.session_state.step_index = 0

if "playback_mode" not in st.session_state:
    st.session_state.playback_mode = "All Steps"


def update_process_count(new_count: int):
    """Callback when number of processes changes."""
    st.session_state.num_processes = new_count
    st.session_state.processes = [f"P{i+1}" for i in range(new_count)]
    # Filter existing events that belong to deleted processes
    st.session_state.event_specs = [
        e for e in st.session_state.event_specs if e.process_id in st.session_state.processes
    ]


def load_preset(preset_name: str):
    """Load pre-configured demo scenarios."""
    if preset_name == "College Demo (Standard 3-Process)":
        eng = SimulationEngine.load_preset_1_college_demo()
        st.session_state.num_processes = 3
        st.session_state.processes = eng.process_ids
        st.session_state.event_specs = eng.event_specs
    elif preset_name == "4-Process Pipeline (Ring)":
        eng = SimulationEngine.load_preset_2_four_processes_cascade()
        st.session_state.num_processes = 4
        st.session_state.processes = eng.process_ids
        st.session_state.event_specs = eng.event_specs
    elif preset_name == "Concurrency & Clock Jump Demo":
        eng = SimulationEngine.load_preset_3_concurrency_clock_jump()
        st.session_state.num_processes = 3
        st.session_state.processes = eng.process_ids
        st.session_state.event_specs = eng.event_specs
    st.session_state.step_index = 0


# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/clock--v1.png", width=64)
    st.title("Simulator Controls")

    # 1. Process Configuration
    st.subheader("1. Process Configuration")
    proc_choice = st.radio(
        "Select Number of Processes:",
        options=[3, 4],
        index=0 if st.session_state.num_processes == 3 else 1,
        horizontal=True,
        key="proc_radio"
    )
    if proc_choice != st.session_state.num_processes:
        update_process_count(proc_choice)
        st.rerun()

    st.info(f"Active Processes: **{', '.join(st.session_state.processes)}**")

    st.markdown("---")

    # 2. Predefined Demos
    st.subheader("2. Demo Scenarios")
    preset_selection = st.selectbox(
        "Select a Predefined Example:",
        [
            "College Demo (Standard 3-Process)",
            "4-Process Pipeline (Ring)",
            "Concurrency & Clock Jump Demo"
        ]
    )
    if st.button("📥 Load Selected Preset", use_container_width=True):
        load_preset(preset_selection)
        st.success(f"Loaded: {preset_selection}")
        st.rerun()

    st.markdown("---")

    # 3. Actions
    st.subheader("3. Simulation Actions")
    col_run, col_reset = st.columns(2)
    with col_run:
        run_clicked = st.button("▶️ Run", use_container_width=True, type="primary")
    with col_reset:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.event_specs = []
            st.session_state.step_index = 0
            st.rerun()

    st.caption("College Mini Project | Distributed Computing")


# -----------------------------------------------------------------------------
# MAIN APP HEADER & LAMPORT RULES BANNER
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">⏱️ Lamport Logical Clock Simulator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'A clean educational simulator demonstrating process synchronization, '
    'happens-before causality (→), and total event ordering in distributed systems.'
    '</div>',
    unsafe_allow_html=True
)

# Lamport Algorithm Rules Expander
with st.expander("📘 Lamport Logical Clock Rules (Click to review theory)", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        **Rule 1: Internal Event**
        $$C_i = C_i + 1$$
        *Before executing an internal action, process $P_i$ increments its local clock.*
        """)
    with c2:
        st.markdown("""
        **Rule 2: Send Message**
        $$C_i = C_i + 1$$
        $$\\text{Attach } T_m = C_i$$
        *Increment local clock and attach timestamp $T_m$ to outgoing message.*
        """)
    with c3:
        st.markdown("""
        **Rule 3: Receive Message**
        $$C_j = \\max(C_j, T_m) + 1$$
        *Update local clock to be greater than both current clock and incoming timestamp.*
        """)


# -----------------------------------------------------------------------------
# VALIDATION ENGINE
# -----------------------------------------------------------------------------
engine = SimulationEngine(process_ids=st.session_state.processes)
engine.event_specs = list(st.session_state.event_specs)
is_valid, errors, warnings = engine.validate()

# Render status
if errors:
    for err in errors:
        st.error(f"⚠️ Validation Error: {err}")
elif warnings:
    for warn in warnings:
        st.warning(f"ℹ️ Notice: {warn}")
else:
    st.success("✅ Event schedule is valid and ready for Lamport execution.")


# -----------------------------------------------------------------------------
# TABS: SIMULATION & EVENT BUILDER & THEORY
# -----------------------------------------------------------------------------
tab_sim, tab_builder, tab_ordering, tab_theory = st.tabs([
    "📊 Simulation & Timeline",
    "✏️ Event Builder & Schedule",
    "🔀 Happens-Before & Total Ordering",
    "🎓 Architecture, Flowchart & Viva Q&A"
])


# -----------------------------------------------------------------------------
# TAB 1: SIMULATION EXECUTION & TIMELINE
# -----------------------------------------------------------------------------
with tab_sim:
    if not is_valid:
        st.info("Please resolve the validation errors above or load a predefined demo from the sidebar.")
    else:
        # Dynamic execution of Lamport Clock algorithm
        sim_result: SimulationResult = engine.run()
        total_steps = len(sim_result.events)

        # Step-by-Step Playback Controls
        st.subheader("Step-by-Step Execution")
        pb_col1, pb_col2, pb_col3, pb_col4 = st.columns([2, 1, 1, 2])

        with pb_col1:
            playback_mode = st.radio(
                "Execution View:",
                ["All Steps at Once", "Interactive Step-by-Step"],
                horizontal=True,
                key="pb_mode"
            )

        if playback_mode == "Interactive Step-by-Step":
            curr_step = st.slider(
                "Execution Step Slider:",
                min_value=1,
                max_value=total_steps,
                value=min(max(1, st.session_state.step_index), total_steps),
                key="step_slider"
            )
            st.session_state.step_index = curr_step
            active_events = sim_result.events[:curr_step]
            curr_snapshot = sim_result.step_snapshots[curr_step - 1]
            last_event = curr_snapshot["current_event"]

            st.markdown(f"""
            > **Current Step {curr_step} of {total_steps}:** Executed **{last_event.event_id}** on **{last_event.process_id}** ({last_event.event_type.value})  
            > *Formula applied:* `{last_event.description}`
            """)
        else:
            active_events = sim_result.events
            st.session_state.step_index = total_steps

        st.markdown("---")

        # ---------------------------------------------------------
        # PROCESS SPACE-TIME TIMELINE (PLOTLY)
        # ---------------------------------------------------------
        st.subheader("Process Space-Time Timeline & Message Flow")

        # Map processes to Y-axis coordinates (P1 highest, P4 lowest)
        p_list = st.session_state.processes
        y_map = {pid: len(p_list) - idx for idx, pid in enumerate(p_list)}

        fig = go.Figure()

        # 1. Draw horizontal process baseline tracks
        for pid in p_list:
            y_val = y_map[pid]
            fig.add_trace(go.Scatter(
                x=[0, total_steps + 1],
                y=[y_val, y_val],
                mode="lines",
                line=dict(color="#CBD5E1", width=3, dash="solid"),
                hoverinfo="skip",
                showlegend=False
            ))

        # 2. Draw message transmission arrows (Send -> Receive)
        send_events_map = {e.message_id: e for e in active_events if e.event_type == EventType.SEND and e.message_id}
        for ev in active_events:
            if ev.event_type == EventType.RECEIVE and ev.message_id in send_events_map:
                send_ev = send_events_map[ev.message_id]
                x0, y0 = send_ev.step_number, y_map[send_ev.process_id]
                x1, y1 = ev.step_number, y_map[ev.process_id]

                # Draw arrow
                fig.add_annotation(
                    x=x1, y=y1,
                    ax=x0, ay=y0,
                    xref="x", yref="y",
                    axref="x", ayref="y",
                    text=f"<b>{ev.message_id}</b> (Tm={send_ev.clock})",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1.5,
                    arrowwidth=2.5,
                    arrowcolor="#8B5CF6",
                    font=dict(color="#6D28D9", size=11),
                    bgcolor="#EDE9FE",
                    borderpad=3
                )

        # 3. Add Event Markers on Process Baselines
        color_map = {
            EventType.INTERNAL: "#0284C7",  # Blue
            EventType.SEND: "#EA580C",      # Orange-Red
            EventType.RECEIVE: "#16A34A"    # Green
        }

        for ev in active_events:
            y_val = y_map[ev.process_id]
            ev_color = color_map.get(ev.event_type, "#4B5563")

            hover_text = (
                f"<b>{ev.event_id} ({ev.process_id})</b><br>"
                f"Type: {ev.event_type.value}<br>"
                f"Previous Clock: {ev.prev_clock}<br>"
                f"New Clock: <b>{ev.clock}</b><br>"
                f"Details: {ev.description}"
            )

            fig.add_trace(go.Scatter(
                x=[ev.step_number],
                y=[y_val],
                mode="markers+text",
                marker=dict(size=24, color=ev_color, line=dict(color="#FFFFFF", width=2)),
                text=[f"<b>{ev.event_id}</b><br>C={ev.clock}"],
                textposition="top center",
                textfont=dict(size=11, color="#1E293B"),
                hoverinfo="text",
                hovertext=[hover_text],
                name=ev.event_type.value,
                showlegend=False
            ))

        # Chart Layout configuration
        fig.update_layout(
            height=380,
            margin=dict(l=60, r=40, t=50, b=40),
            xaxis=dict(
                title="Simulation Execution Step",
                tickmode="linear",
                tick0=1,
                dtick=1,
                range=[0, total_steps + 1.2],
                gridcolor="#F1F5F9"
            ),
            yaxis=dict(
                title="Process",
                tickvals=[y_map[pid] for pid in p_list],
                ticktext=[f"<b>{pid}</b>" for pid in p_list],
                range=[0.5, len(p_list) + 0.8],
                gridcolor="#F8FAFC"
            ),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Legend indicator
        leg_c1, leg_c2, leg_c3 = st.columns(3)
        with leg_c1:
            st.markdown('<span class="badge-internal">● Internal Event</span> (C = C + 1)', unsafe_allow_html=True)
        with leg_c2:
            st.markdown('<span class="badge-send">● Send Message</span> (C = C + 1, Tm = C)', unsafe_allow_html=True)
        with leg_c3:
            st.markdown('<span class="badge-receive">● Receive Message</span> (C = max(C, Tm) + 1)', unsafe_allow_html=True)

        st.markdown("---")

        # ---------------------------------------------------------
        # EVENT TABLE
        # ---------------------------------------------------------
        st.subheader("Lamport Logical Clock Event Table")
        table_data = [e.to_dict() for e in active_events]
        df_events = pd.DataFrame(table_data)
        st.dataframe(df_events, use_container_width=True, hide_index=True)

        # ---------------------------------------------------------
        # MESSAGE COMMUNICATION SUMMARY CARDS
        # ---------------------------------------------------------
        if sim_result.messages:
            st.subheader("Message Communication Flow")
            msg_cols = st.columns(len(sim_result.messages))
            for idx, (m_id, msg) in enumerate(sim_result.messages.items()):
                with msg_cols[idx % len(msg_cols)]:
                    status_badge = "✅ Delivered" if msg.is_delivered else "⏳ In-Flight"
                    st.metric(
                        label=f"Message {msg.message_id}: {msg.source_process} ➔ {msg.target_process}",
                        value=f"Timestamp Tm = {msg.sent_timestamp}",
                        delta=f"Delivered at C = {msg.delivery_clock}" if msg.is_delivered else "In-transit"
                    )


# -----------------------------------------------------------------------------
# TAB 2: INTERACTIVE EVENT BUILDER & SCHEDULE
# -----------------------------------------------------------------------------
with tab_builder:
    st.subheader("Event Schedule Configuration")
    st.caption("Inspect, add, or delete events dynamically. Clocks will automatically recalculate.")

    # Form to add a new event
    with st.expander("➕ Add New Event", expanded=False):
        with st.form("add_event_form", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                new_eid = st.text_input("Event ID (e.g. E8):", value=f"E{len(st.session_state.event_specs) + 1}")
            with f_col2:
                new_pid = st.selectbox("Process:", options=st.session_state.processes)
            with f_col3:
                new_etype = st.selectbox("Event Type:", ["Internal", "Send", "Receive"])

            f_msg_id = ""
            f_target = None
            f_source = None

            if new_etype == "Send":
                m_c1, m_c2 = st.columns(2)
                with m_c1:
                    f_msg_id = st.text_input("Message ID (e.g. M3):", value="M3")
                with m_c2:
                    available_targets = [p for p in st.session_state.processes if p != new_pid]
                    f_target = st.selectbox("Target Process:", options=available_targets)
            elif new_etype == "Receive":
                m_c1, m_c2 = st.columns(2)
                with m_c1:
                    f_msg_id = st.text_input("Message ID to Receive (e.g. M3):", value="M3")
                with m_c2:
                    available_sources = [p for p in st.session_state.processes if p != new_pid]
                    f_source = st.selectbox("Source Process:", options=available_sources)

            f_desc = st.text_input("Description / Notes (Optional):", value="")

            submitted = st.form_submit_button("Add Event to Schedule", use_container_width=True)
            if submitted:
                e_type_enum = {
                    "Internal": EventType.INTERNAL,
                    "Send": EventType.SEND,
                    "Receive": EventType.RECEIVE
                }[new_etype]

                new_spec = EventSpec(
                    event_id=new_eid.strip(),
                    process_id=new_pid,
                    event_type=e_type_enum,
                    message_id=f_msg_id.strip() if f_msg_id else None,
                    target_process=f_target,
                    source_process=f_source,
                    custom_desc=f_desc.strip()
                )
                st.session_state.event_specs.append(new_spec)
                st.success(f"Added event {new_eid}!")
                st.rerun()

    # Display configured schedule table with delete options
    if st.session_state.event_specs:
        sched_data = []
        for idx, spec in enumerate(st.session_state.event_specs):
            sched_data.append({
                "Seq #": idx + 1,
                "Event ID": spec.event_id,
                "Process": spec.process_id,
                "Event Type": spec.event_type.value,
                "Message ID": spec.message_id or "-",
                "Target / Source": spec.target_process or spec.source_process or "-",
                "Description": spec.custom_desc
            })
        st.dataframe(pd.DataFrame(sched_data), use_container_width=True, hide_index=True)

        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            del_idx = st.selectbox(
                "Select Event to Remove:",
                options=list(range(len(st.session_state.event_specs))),
                format_func=lambda i: f"#{i+1}: {st.session_state.event_specs[i].summary()}"
            )
        with del_col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Delete Event", use_container_width=True):
                st.session_state.event_specs.pop(del_idx)
                st.rerun()
    else:
        st.info("No events configured yet. Click above to add an event or load a demo preset.")


# -----------------------------------------------------------------------------
# TAB 3: HAPPENS-BEFORE & TOTAL ORDERING
# -----------------------------------------------------------------------------
with tab_ordering:
    st.subheader("Event Ordering & Causality Analysis")

    if not is_valid:
        st.warning("Fix validation errors to view ordering and causality.")
    else:
        sim_res = engine.run()

        col_to, col_causal = st.columns(2)

        # Lamport Total Order Table
        with col_to:
            st.markdown("#### 1. Lamport Total Order ($a \\Rightarrow b$)")
            st.caption(
                "Tie-breaking rule: If $C(a) == C(b)$, the event on the lower process ID "
                "is ordered earlier ($P1 < P2 < P3 < P4$)."
            )

            total_order_data = []
            for rank, ev in enumerate(sim_res.total_order, start=1):
                total_order_data.append({
                    "Total Rank": rank,
                    "Event ID": ev.event_id,
                    "Process": ev.process_id,
                    "Clock (C)": ev.clock,
                    "Type": ev.event_type.value
                })
            st.dataframe(pd.DataFrame(total_order_data), use_container_width=True, hide_index=True)

        # Interactive Pair Causality Checker
        with col_causal:
            st.markdown("#### 2. Happens-Before Causality Checker")
            st.caption("Select any two events to inspect their causal relationship:")

            e_list = [e.event_id for e in sim_res.events]
            sel_c1, sel_c2 = st.columns(2)
            with sel_c1:
                ev_a = st.selectbox("Event A:", options=e_list, index=0)
            with sel_c2:
                ev_b = st.selectbox("Event B:", options=e_list, index=min(1, len(e_list) - 1))

            rel = sim_res.causality_matrix.get((ev_a, ev_b), "Unknown")

            if "Happened Before" in rel:
                st.success(f"**{rel}**  \nEvent **{ev_a}** causally precedes **{ev_b}** ($a \\to b$).")
            elif "Happened After" in rel:
                st.info(f"**{rel}**  \nEvent **{ev_b}** causally precedes **{ev_a}** ($b \\to a$).")
            elif "Concurrent" in rel:
                st.warning(
                    f"**{rel}**  \nEvents **{ev_a}** and **{ev_b}** are **concurrent** ($a \\parallel b$). "
                    f"Neither event had causal knowledge of the other when it occurred!"
                )
            else:
                st.write(f"Result: {rel}")

            # Explanation of Causality vs Lamport Clocks
            st.markdown("""
            > **Viva Key Point:**  
            > In Lamport Logical Clocks:  
            > $$a \\to b \\implies C(a) < C(b)$$  
            > **However**, the converse is **NOT** necessarily true:  
            > $$C(a) < C(b) \\;\\;\\not\\!\\implies a \\to b$$  
            > Two events may have different clock values and still be completely concurrent!
            """)

        st.markdown("---")
        st.markdown("#### Complete Pairwise Causality Matrix")
        # Build pairwise DataFrame
        e_names = [e.event_id for e in sim_res.events]
        matrix_rows = []
        for e1 in e_names:
            row = {"Event": e1}
            for e2 in e_names:
                r_val = sim_res.causality_matrix.get((e1, e2), "")
                if "Happened Before" in r_val:
                    row[e2] = "→"
                elif "Happened After" in r_val:
                    row[e2] = "←"
                elif "Concurrent" in r_val:
                    row[e2] = "|| (Concurrent)"
                else:
                    row[e2] = "="
            matrix_rows.append(row)

        st.dataframe(pd.DataFrame(matrix_rows).set_index("Event"), use_container_width=True)
        st.caption("Legend: `→` Row happened before Column | `←` Row happened after Column | `||` Concurrent | `=` Identical event")


# -----------------------------------------------------------------------------
# TAB 4: ARCHITECTURE, FLOWCHART & VIVA PREPARATION
# -----------------------------------------------------------------------------
with tab_theory:
    st.subheader("System Architecture & Algorithm Flowchart")

    # Flowchart rendering using Graphviz
    col_fc, col_arch = st.columns(2)

    with col_fc:
        st.markdown("#### Lamport Clock Algorithm Flowchart")
        st.graphviz_chart("""
        digraph LamportAlgorithm {
            rankdir=TB;
            node [shape=box, style="filled,rounded", fontname="Helvetica", fillcolor="#F8FAFC", color="#64748B"];
            edge [fontname="Helvetica", color="#475569"];

            start [label="Event Occurs at Process Pi", shape=oval, fillcolor="#E0E7FF", color="#4338CA"];
            check_type [label="What is the Event Type?", shape=diamond, fillcolor="#FEF3C7", color="#D97706"];
            
            internal [label="Internal Event:\\nCi = Ci + 1", fillcolor="#E0F2FE", color="#0284C7"];
            send [label="Send Event:\\nCi = Ci + 1\\nAttach Tm = Ci to message", fillcolor="#FFEDD5", color="#EA580C"];
            receive [label="Receive Event with Tm:\\nCi = max(Ci, Tm) + 1", fillcolor="#DCFCE7", color="#16A34A"];
            
            record [label="Record Event in Log &\\nUpdate Process Timeline", fillcolor="#F1F5F9", color="#475569"];
            order [label="Compute Total Order &\\nHappens-Before Relation (->)", fillcolor="#EDE9FE", color="#7C3AED"];

            start -> check_type;
            check_type -> internal [label=" Internal"];
            check_type -> send [label=" Send"];
            check_type -> receive [label=" Receive"];
            
            internal -> record;
            send -> record;
            receive -> record;
            record -> order;
        }
        """)

    with col_arch:
        st.markdown("#### Mini Project System Architecture")
        st.graphviz_chart("""
        digraph SystemArchitecture {
            rankdir=TB;
            node [shape=box, style="filled,rounded", fontname="Helvetica"];
            edge [fontname="Helvetica", color="#475569"];

            ui [label="Streamlit User Interface (app.py)\\n• Process Config & Event Builder\\n• Plotly Space-Time Diagram\\n• Step-by-Step Interactive Controls", fillcolor="#EFF6FF", color="#3B82F6"];
            validator [label="Validation Engine (simulator.py)\\n• Validates Process IDs\\n• Checks Causality & Message Ordering\\n• Rejects Duplicates / Missing Sends", fillcolor="#FEF3C7", color="#D97706"];
            sim_engine [label="Simulation Engine (simulator.py)\\n• Orchestrates Event Execution\\n• Computes Transitive Closure (DAG)\\n• Generates Step Snapshots", fillcolor="#F3E8FF", color="#9333EA"];
            core [label="Lamport Core (lamport_clock.py)\\n• LamportProcess Class\\n• Event & Message Dataclasses\\n• Rules: C=C+1, C=max(C,Tm)+1", fillcolor="#DCFCE7", color="#16A34A"];

            ui -> validator [label=" Event Specifications"];
            validator -> sim_engine [label=" Validated Schedule"];
            sim_engine -> core [label=" Executes Clock Rules"];
            core -> sim_engine [label=" Clocks & Events"];
            sim_engine -> ui [label=" Simulation Results, Order, Matrix"];
        }
        """)

    st.markdown("---")

    # ---------------------------------------------------------
    # VIVA QUESTIONS AND ANSWERS ACCORDION
    # ---------------------------------------------------------
    st.subheader("🎓 Viva Preparation Guide (16 Key Questions & Answers)")
    st.caption("Curated specifically for your Distributed Computing lab and viva examination:")

    viva_qa = [
        (
            "1. What is a Distributed System?",
            "A distributed system is a collection of autonomous computing entities (processes/nodes) that communicate "
            "over a network via message passing and coordinate their actions by sharing messages to appear as a single coherent system to the end user. "
            "It lacks shared memory and a global physical clock."
        ),
        (
            "2. Why can't we rely on physical clocks in distributed systems?",
            "Every computer has a quartz crystal clock that experiences physical clock drift due to temperature, voltage, and age differences. "
            "Network latency makes exact synchronization impossible without error (as governed by relativistic and network limits). Hence, "
            "physical timestamps cannot reliably order events across independent machines without advanced hardware like atomic clocks."
        ),
        (
            "3. What is a Logical Clock?",
            "A logical clock is a monotonically increasing software counter maintained by each distributed process to capture the chronological "
            "or causal ordering of events without relying on physical time. Proposed by Leslie Lamport in his seminal 1978 paper."
        ),
        (
            "4. What is the Happens-Before Relation (denoted as '→')?",
            "The happens-before relation (defined by Leslie Lamport) defines a partial ordering of events in a distributed system:\n"
            "1. If events a and b belong to the same process and a occurs before b, then a → b.\n"
            "2. If event a is sending a message and event b is receiving that message, then a → b.\n"
            "3. If a → b and b → c, then a → c (transitivity).\n"
            "If neither a → b nor b → a holds, the events are concurrent (a || b)."
        ),
        (
            "5. State the three updating rules for Lamport Logical Clocks.",
            "1. Internal Event: Ci = Ci + 1\n"
            "2. Send Event: Ci = Ci + 1, and attach timestamp Tm = Ci to message m.\n"
            "3. Receive Event: When receiving message m with timestamp Tm, the process updates: Cj = max(Cj, Tm) + 1."
        ),
        (
            "6. Why is the '+ 1' required in the receive rule C = max(C, Tm) + 1?",
            "Because message delivery takes a non-zero amount of time, the receive event must strictly succeed the send event in logical time. "
            "Therefore, the receiver clock must be strictly greater than Tm (i.e. Cj > Tm), ensuring that if a is the send event and b is the receive event, C(a) < C(b)."
        ),
        (
            "7. Does Lamport's Clock satisfy the Clock Condition?",
            "Yes. The Clock Condition states: For any events a and b, if a → b then C(a) < C(b). Lamport's algorithm is mathematically proven to satisfy this condition."
        ),
        (
            "8. Does C(a) < C(b) imply that a happened before b (a → b)?",
            "NO! This is the most famous viva question. Lamport clocks guarantee only the forward implication (a → b ⇒ C(a) < C(b)). "
            "If C(a) < C(b), event a might have happened before b, OR events a and b might be completely CONCURRENT (a || b). Lamport clocks cannot detect causality backwards."
        ),
        (
            "9. How does Vector Clock solve the limitation of Lamport Clock?",
            "A Vector Clock maintains an array of clocks (one entry for each process). For Vector Clocks: V(a) < V(b) IF AND ONLY IF a → b. "
            "Vector clocks provide an exact characterization of causal precedence, allowing the system to determine if two events are concurrent."
        ),
        (
            "10. How does Lamport define a Total Order on events?",
            "Lamport defines total order (denoted ⇒) by breaking ties using unique process identifiers:\n"
            "a ⇒ b iff (C(a) < C(b)) OR (C(a) == C(b) AND Process_ID(a) < Process_ID(b)).\n"
            "This creates an arbitrary but universally agreed consistent total order across all processes."
        ),
        (
            "11. What is an example of an application that requires Total Ordering?",
            "Distributed Mutual Exclusion (e.g., Lamport's Bakery algorithm or Ricart-Agrawala algorithm) and replicated state machines (consensus protocols like Raft or Paxos) "
            "require all replicas to apply state mutations in the exact same total order."
        ),
        (
            "12. What does it mean for two events to be 'Concurrent'?",
            "Two events a and b are concurrent (written a || b) if neither event causally influences the other: a does not happen before b, and b does not happen before a. "
            "They could have physically occurred at the exact same instant or at completely different physical times without knowing about each other."
        ),
        (
            "13. What is Causality Violation in message passing?",
            "A causality violation occurs when a process receives a message before it was sent, or receives an effect before its cause (e.g. receiving a reply to a request before receiving the original request). "
            "Our simulator explicitly validates and rejects any schedule where a receive event precedes its corresponding send event."
        ),
        (
            "14. What is Clock Drift vs Clock Skew?",
            "Clock Skew is the instantaneous difference in readings between two physical clocks at a given point in time.\n"
            "Clock Drift is the rate of change of clock skew over time caused by variations in quartz oscillator frequencies."
        ),
        (
            "15. What are the limitations of Lamport Logical Clocks?",
            "1. Cannot detect concurrency (C(a) < C(b) does not imply a → b).\n"
            "2. Total ordering tie-breaking is arbitrary (based on Process ID, not real causality).\n"
            "3. Monotonically increasing integers can grow without bound over time.\n"
            "4. Does not provide physical elapsed time (cannot tell how many real seconds elapsed)."
        ),
        (
            "16. How does your simulator validate input events before execution?",
            "Our simulator validates:\n"
            "• Unknown or invalid process IDs.\n"
            "• Duplicate event IDs.\n"
            "• Duplicate message IDs.\n"
            "• Receiving a message before it is sent (causality violation).\n"
            "• Receiving a message that was never sent.\n"
            "• Mismatch between message target process and receiver process."
        )
    ]

    for question, answer in viva_qa:
        with st.expander(f"❓ {question}"):
            st.markdown(f"**Answer:**\n{answer}")
