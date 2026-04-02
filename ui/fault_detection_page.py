"""
Fault Detection Dashboard — Modular Implementation
==================================================
This is the main entry point for the Fault Detection page, delegating
logic to the ui.lib.fault_detection package for better maintainability.
"""

import streamlit as st
import os
import time
from typing import Dict, Any, List

# Import modular library
from ui.lib.fault_detection import (
    FaultDetectionAPI, 
    UIStateManager, 
    CUSTOM_CSS,
    COLORS
)
from ui.lib.fault_detection.components import (
    GaugeComponent,
    VisualizationComponent,
    DigitalTwinComponent,
    AnalysisComponent
)

# ─── Configuration ───────────────────────────────────────────────────────────
API_HOST = os.environ.get("API_URL", "http://localhost:8000")
API_BASE_URL = f"{API_HOST}/api/v1"

# Initialize Client and State Manager
if "fd_api" not in st.session_state:
    st.session_state.fd_api = FaultDetectionAPI(API_BASE_URL)
api = st.session_state.fd_api
state_mgr = UIStateManager()

def render_fault_detection_page():
    """Main entry point for the Fault Detection dashboard."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # ─── Sidebar: System Control & Site Selection ────────────────────────────
    st.sidebar.markdown("### 🔧 System Control")
    
    if not api.check_connection():
        st.sidebar.error("❌ API Offline")
        st.error("Cannot connect to the Fault Detection backend. Please check if the API is running.")
        return

    # Fetch Sites (Cities)
    cities = api.get_cities()
    if not cities:
        st.warning("No sites available in the engine configuration.")
        return

    city_names = [c["name"] for c in cities]
    selected_city_name = st.sidebar.selectbox("🏙️ Select Region/City", city_names, index=0)
    selected_city = next(c for c in cities if c["name"] == selected_city_name)
    
    # Fetch Region State
    region_data = api.get_region_state(selected_city_name)
    factories = region_data.get("factories", [])
    
    if not factories:
        st.info(f"No factories found in {selected_city_name}.")
        return

    factory_ids = [f["factory_id"] for f in factories]
    selected_factory_id = st.sidebar.selectbox("🏭 Select Specific Site", factory_ids, index=0)
    
    # Control Buttons
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    if col1.button("▶️ Tick", use_container_width=True):
        api.tick_simulation(selected_city_name)
    if col2.button("🧹 Clear", use_container_width=True):
        api.clear_faults(selected_city_name)

    # Fault Injection
    with st.sidebar.expander("🚨 Manual Fault Injection", expanded=False):
        f_type = st.selectbox("Type", ["LINE_FAULT", "BATTERY_FAULT", "ARC_FAULT"])
        f_severity = st.slider("Severity", 0.0, 1.0, 0.5)
        if st.button("🔥 Inject Fault", use_container_width=True):
            if api.inject_fault(selected_city_name, selected_factory_id, f_type, f_severity):
                state_mgr.add_fault_event(selected_factory_id, f_type, f_severity)
                st.toast( f"Injected {f_type} into {selected_factory_id}")

    # ─── Update State ────────────────────────────────────────────────────────
    # Store history for current site
    for f in factories:
        state_mgr.update_from_api(f["factory_id"], f)
    
    current_site_state = state_mgr.get_site_state(selected_factory_id)
    fault_info = api.get_fault_info(selected_city_name)

    # ─── Main Dashboard Header ───────────────────────────────────────────────
    st.markdown(f"## 🛡️ Fault Detection — {selected_city_name} Node")
    st.markdown(f"**Site Status:** `{current_site_state['fault_class']}` | "
                f"**Monitoring:** `{selected_factory_id}`")

    # High-level Alert
    AnalysisComponent.render_fault_alert(fault_info)

    # ─── Layout: Summary Metrics ─────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        GaugeComponent.render_metric_card("System Voltage", f"{current_site_state['current_voltage']:.1f}", "Volts DC", COLORS["voltage"])
    with m2:
        GaugeComponent.render_metric_card("Power Output", f"{current_site_state['current_power']:.2f}", "kW", COLORS["accent"])
    with m3:
        GaugeComponent.render_metric_card("Node Current", f"{current_site_state['current_current']:.1f}", "Amps", COLORS["warning"])
    with m4:
        GaugeComponent.render_metric_card("Confidence", f"{current_site_state['fault_confidence']*100:.0f}", "% Accurate", COLORS["success"])

    # ─── Layout: Main Features ───────────────────────────────────────────────
    tab_overview, tab_wavelet, tab_analysis, tab_digital_twin = st.tabs([
        "📈 Live Status", "🌊 Wavelet Analysis", "📋 Fault Log", "🧩 Digital Twin"
    ])

    with tab_overview:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### ⚡ Real-time Voltage Waveform")
            VisualizationComponent.render_voltage_waveform(current_site_state["voltage_history"])
        with c2:
            st.markdown("#### 🔋 Battery Telemetry")
            GaugeComponent.render_soc_gauge(current_site_state["current_soc"], "Storage SoC")
            GaugeComponent.render_speedometer(current_site_state["current_temperature"], "Temp", 0, 100, "°C")
            GaugeComponent.render_fault_badge(current_site_state["fault_class"], current_site_state["fault_confidence"])

    with tab_wavelet:
        st.markdown("#### 🌊 Sub-band Energy Distribution (D1-D4, A4)")
        VisualizationComponent.render_dwt_energy_spectrum(current_site_state["detector_state"])
        st.info("The DWT energy spectrum highlights high-frequency transients typical of line faults and sensor drifting.")

    with tab_analysis:
        st.markdown("#### 📜 historical Event Timeline")
        AnalysisComponent.render_timeline(st.session_state.get("fd_fault_events", []))
        st.markdown("#### 🔍 Structural Classification Details")
        AnalysisComponent.render_analysis_details(current_site_state.get("analysis", {}))

    with tab_digital_twin:
        st.markdown(f"#### 🏗️ Digital Twin — {selected_factory_id} Internal Circuit")
        # Fetch detailed topology for this specific factory
        circuit_info = api.get_circuit_info(selected_city_name, node_id=selected_factory_id)
        
        # Prepare node status for schematic coloring
        node_status = {}
        for f in factories:
            node_status[f["factory_id"]] = {
                "voltage": f["battery"]["voltage"],
                "status": f["fault"]["fault_class"]
            }
            # For factories, their internal nodes are also monitored by the engine loosely
            # mapping them to the main status
            node_status[f"{f['factory_id']}_main"] = node_status[f["factory_id"]]
            node_status[f"{f['factory_id']}_pv"] = node_status[f["factory_id"]]
            node_status[f"{f['factory_id']}_bat"] = node_status[f["factory_id"]]

        DigitalTwinComponent.render_schematic(circuit_info, fault_info, node_status)

if __name__ == "__main__":
    st.set_page_config(page_title="Fault Detection Dashboard", layout="wide")
    render_fault_detection_page()