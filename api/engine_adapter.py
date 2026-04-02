import logging
import time
import threading
import numpy as np
from typing import Dict, List, Any, Optional
from collections import deque

# Import core engine components
from dc_microgrid_dwt.src.framework.bus import EventBus
from dc_microgrid_dwt.src.framework.registry import AgentRegistry
from dc_microgrid_dwt.src.framework.observability import Observability
from dc_microgrid_dwt.src.domain.events import (
    VoltageSampleEvent, DWTResultEvent, FaultDetectedEvent,
    FaultInjectionEvent, SystemTripEvent, GridTopologyEvent
)
from dc_microgrid_dwt.src.agents.ingestion.sampler import SamplerAgent
from dc_microgrid_dwt.src.agents.ingestion.window_manager import WindowManagerAgent
from dc_microgrid_dwt.src.agents.processing.dwt_engine import DWTEngineAgent
from dc_microgrid_dwt.src.agents.detection.fault_voter import FaultVoterAgent
from dc_microgrid_dwt.src.agents.control.telemetry import TelemetryAgent

logger = logging.getLogger("EngineAdapter")

class EngineAdapter:
    """
    Bridge between FastAPI and the dc_microgrid_dwt agent-based engine.
    
    Manages the lifecycle of the engine agents and provides a simplified
    API for the web dashboard.
    """
    
    def __init__(self, region: str, factories: List[Dict[str, Any]]):
        self.region = region
        self.factories_config = factories
        self.bus = EventBus()
        self.registry = AgentRegistry()
        self.obs = Observability.get_instance()
        
        # Internal state tracking
        self.node_states: Dict[str, Dict[str, Any]] = {}
        self.voltage_history: Dict[str, deque] = {}
        self.dwt_energies: Dict[str, Dict[str, float]] = {}
        self.active_faults: Dict[str, Dict[str, Any]] = {}
        self.topology: Dict[str, Any] = {"nodes": {}, "connections": []}
        
        # Initialize state for each factory
        for f in factories:
            fid = f['name']
            self.node_states[fid] = {
                "voltage": 400.0,
                "current": 0.0,
                "soc": f.get("initial_soc", 0.5),
                "status": "NORMAL",
                "last_update": time.time()
            }
            self.voltage_history[fid] = deque(maxlen=300)
            self.dwt_energies[fid] = {"D1": 0, "D2": 0, "D3": 0, "D4": 0, "A4": 0}
        
        # Setup Agents
        self._init_agents()
        
        # Subscribe to relevant events for state tracking
        self.bus.subscribe(VoltageSampleEvent, self._on_voltage_sample)
        self.bus.subscribe(DWTResultEvent, self._on_dwt_result)
        self.bus.subscribe(FaultDetectedEvent, self._on_fault_detected)
        self.bus.subscribe(GridTopologyEvent, self._on_topology_update)
        
        # Start the engine
        self.registry.start_all()
        logger.info(f"EngineAdapter initialized for region: {region}")

    def _init_agents(self):
        """Initialize and register engine agents."""
        dsp_cfg = {
            'sampling': {'rate_hz': 20000, 'window_size': 128},
            'wavelet': {'family': 'db4', 'level': 4}
        }
        
        # We create a set of agents that monitor the whole region
        # In a real system, we might have agents per node, but here we share
        self.sampler = SamplerAgent("Sampler", self.bus, dsp_cfg)
        self.window_mgr = WindowManagerAgent("WindowManager", self.bus, dsp_cfg)
        self.dwt_engine = DWTEngineAgent("DWTEngine", self.bus, dsp_cfg)
        self.voter = FaultVoterAgent("FaultVoter", self.bus)
        self.telemetry = TelemetryAgent("Telemetry", self.bus)
        
        agents = [self.sampler, self.window_mgr, self.dwt_engine, self.voter, self.telemetry]
        for a in agents:
            self.registry.register(a)

    def _on_voltage_sample(self, event: VoltageSampleEvent):
        """Handle incoming voltage samples."""
        fid = event.node_id
        if fid in self.node_states:
            self.node_states[fid]["voltage"] = event.voltage
            self.node_states[fid]["current"] = event.current
            self.voltage_history[fid].append(event.voltage)

    def _on_dwt_result(self, event: DWTResultEvent):
        """Handle DWT analysis results."""
        # For now, we update the primary node or the one specified in metadata
        # In a real multi-node engine, the event would have a node_id
        node_id = getattr(event, 'node_id', list(self.node_states.keys())[0])
        if node_id in self.dwt_energies:
            self.dwt_energies[node_id] = event.energy_levels

    def _on_fault_detected(self, event: FaultDetectedEvent):
        """Handle fault detection events."""
        node_id = getattr(event, 'node_id', list(self.node_states.keys())[0])
        self.active_faults[node_id] = {
            "type": event.fault_type,
            "severity": event.severity,
            "confidence": event.confidence,
            "timestamp": event.timestamp
        }
        if event.severity > 0.3:
            self.node_states[node_id]["status"] = "FAULT"
        else:
            self.node_states[node_id]["status"] = "NORMAL"

    def _on_topology_update(self, event: GridTopologyEvent):
        """Handle grid topology updates."""
        self.topology = {
            "nodes": event.nodes,
            "connections": event.connections
        }

    def tick(self, iterations: int = 1):
        """Advance the simulation by N steps."""
        for _ in range(iterations):
            # In a real system, the sampler agent would pull from a sensor
            # Here, we can manually trigger a sample for each node
            for fid in self.node_states:
                # Generate synthetic data with some noise
                base_v = 400.0
                if fid in self.active_faults and self.active_faults[fid]["severity"] > 0.5:
                    base_v = 360.0 + np.random.normal(0, 10.0)
                
                v = base_v + np.random.normal(0, 0.5)
                i = (v / 40.0) + np.random.normal(0, 0.1)
                
                evt = VoltageSampleEvent(voltage=v, current=i, node_id=fid)
                self.bus.publish(evt)
            
            # Allow agents to process
            time.sleep(0.001)

    def inject_fault(self, factory_id: str, fault_type: str, severity: float):
        """Inject a fault into the engine."""
        evt = FaultInjectionEvent(
            fault_type=fault_type,
            severity=severity,
            location=factory_id
        )
        self.bus.publish(evt)
        logger.info(f"Injected {fault_type} fault into {factory_id} with severity {severity}")

    def _generate_factory_circuit(self, fid: str, ftype: str) -> Dict[str, Any]:
        """Generate a unique internal circuit for a factory based on its type."""
        # Common nodes
        buses = [
            {"id": f"{fid}_pcc", "name": "PCC", "x": 100, "y": 250, "type": "Slack"},
            {"id": f"{fid}_main", "name": "Main Bus", "x": 300, "y": 250, "type": "PQ"},
        ]
        lines = [
            {"from_bus": f"{fid}_pcc", "to_bus": f"{fid}_main", "r_ohm": 0.05, "length_km": 0.02}
        ]
        generators = []
        loads = []

        if ftype == "solar":
            # SolarFarm: PV -> DC Bus -> Main
            buses.append({"id": f"{fid}_pv", "name": "PV Array", "x": 500, "y": 150, "type": "PV"})
            lines.append({"from_bus": f"{fid}_pv", "to_bus": f"{fid}_main", "r_ohm": 0.02, "length_km": 0.01})
            generators.append({"id": f"{fid}_gen", "bus_id": f"{fid}_pv", "p_mw": 5.0})
        elif ftype == "wind":
            # WindFarm: Turbine -> Main
            buses.append({"id": f"{fid}_wt", "name": "Wind Turbine", "x": 500, "y": 150, "type": "PV"})
            lines.append({"from_bus": f"{fid}_wt", "to_bus": f"{fid}_main", "r_ohm": 0.03, "length_km": 0.05})
            generators.append({"id": f"{fid}_gen", "bus_id": f"{fid}_wt", "p_mw": 10.0})
        
        # All factories have a battery and a local load
        buses.append({"id": f"{fid}_bat", "name": "ESS", "x": 500, "y": 350, "type": "PQ"})
        lines.append({"from_bus": f"{fid}_bat", "to_bus": f"{fid}_main", "r_ohm": 0.01, "length_km": 0.005})
        
        buses.append({"id": f"{fid}_load", "name": "Local Load", "x": 300, "y": 400, "type": "PQ"})
        lines.append({"from_bus": f"{fid}_main", "to_bus": f"{fid}_load", "r_ohm": 0.01, "length_km": 0.005})
        loads.append({"id": f"{fid}_ld", "bus_id": f"{fid}_load", "p_mw": 2.0})

        return {
            "name": f"Circuit_{fid}",
            "buses": buses,
            "lines": lines,
            "generators": generators,
            "loads": loads
        }

    def get_topology(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the grid topology. 
        If node_id is provided, returns the internal circuit of that factory.
        Otherwise, returns the regional grid topology.
        """
        if node_id:
            # Find factory config
            config = next((f for f in self.factories_config if f['name'] == node_id), None)
            if config:
                return self._generate_factory_circuit(node_id, config['type'])
            
        # Regional topology (default)
        if not self.topology or not self.topology.get("nodes"):
            # Return a default topology based on the configured factories
            nodes = []
            lines = []
            for i, (fid, state) in enumerate(self.node_states.items()):
                nodes.append({
                    "id": fid,
                    "bus_id": fid,
                    "name": fid,
                    "x": 100 + (i * 200),
                    "y": 250 + (50 if i % 2 == 0 else -50),
                    "type": "PQ"
                })
                if i > 0:
                    prev_fid = list(self.node_states.keys())[i-1]
                    lines.append({
                        "from_bus": prev_fid,
                        "to_bus": fid,
                        "r_ohm": 0.1,
                        "length_km": 0.5
                    })
            return {
                "name": f"Grid_{self.region}",
                "buses": nodes,
                "lines": lines,
                "generators": [{"id": f"G_{fid}", "bus_id": fid} for fid in self.node_states],
                "loads": [{"id": f"L_{fid}", "bus_id": fid} for fid in self.node_states]
            }
        return self.topology

    def clear_faults(self):
        """Clear all faults."""
        self.active_faults.clear()
        for fid in self.node_states:
            self.node_states[fid]["status"] = "NORMAL"
        # We would also publish a clear event if the agents support it
        logger.info("Cleared all faults in engine")

    def get_dashboard_state(self) -> Dict[str, Any]:
        """Collect all current state for the FastAPI response."""
        factories_state = []
        for fid, config in zip(self.node_states.keys(), self.factories_config):
            state = self.node_states[fid]
            fault = self.active_faults.get(fid, {"type": "NORMAL", "severity": 0, "confidence": 0, "timestamp": 0})
            
            # Simple SoC simulation for the dashboard
            old_soc = state["soc"]
            new_soc = np.clip(old_soc - (0.0001 if state["current"] > 0 else -0.00005), 0.1, 0.95)
            state["soc"] = new_soc
            
            factories_state.append({
                "factory_id": fid,
                "type": config["type"],
                "capacity_kw": config["capacity_kw"],
                "battery": {
                    "factory_id": fid,
                    "soc": state["soc"],
                    "soc_pct": state["soc"] * 100,
                    "voltage": state["voltage"],
                    "current": state["current"],
                    "temperature": 25.0 + (state["current"] * 2.0),
                    "energy_in_kwh": 0.0, # Dummy for now
                    "energy_out_kwh": 0.0,
                    "peak_charge_kw": 100.0,
                    "peak_discharge_kw": 100.0
                },
                "power_history": [state["voltage"] * state["current"] / 1000.0] * 10, # Minimal history
                "voltage_history": list(self.voltage_history[fid]),
                "soc_history": [state["soc"]] * 10,
                "fault": {
                    "class": fault["type"],
                    "confidence": fault["confidence"],
                    "severity": int(fault["severity"] * 5),
                    "explanation": f"Engine detected {fault['type']}" if fault["severity"] > 0 else "System Normal",
                    "power_anomaly": fault["severity"] > 0.4,
                    "voltage_anomaly": fault["severity"] > 0.3,
                    "current_anomaly": fault["severity"] > 0.5,
                    "battery_anomaly": fault["type"] == "BATTERY_FAULT"
                },
                "wavelet_features": {
                    "energies": [self.dwt_energies[fid].get(k, 0) for k in ["D1", "D2", "D3", "D4", "A4"]],
                    "energy_ratios": [0.1, 0.2, 0.3, 0.4], # Dummy
                    "kurtosis": [1.0, 1.1, 1.2, 1.3, 1.4], # Dummy
                    "total_energy": sum(self.dwt_energies[fid].values()),
                    "high_freq_ratio": 0.5,
                    "low_freq_ratio": 0.5
                }
            })
            
        return {
            "region": self.region,
            "tick_count": self.bus.get_stats()["total_events"],
            "uptime_seconds": time.time() - self.bus._start_time,
            "factories": factories_state,
            "summary": {
                "total_factories": len(factories_state),
                "fault_counts": self._calculate_fault_counts(factories_state),
                "health_score": self._calculate_health_score(factories_state),
                "max_severity": max((f["fault"]["severity"] for f in factories_state), default=0),
                "critical_factory": self._get_critical_factory(factories_state)
            }
        }

    def _calculate_fault_counts(self, factories):
        counts = {}
        for f in factories:
            fc = f["fault"]["class"]
            counts[fc] = counts.get(fc, 0) + 1
        return counts

    def _calculate_health_score(self, factories):
        if not factories: return 100.0
        normal = sum(1 for f in factories if f["fault"]["class"] == "NORMAL")
        return (normal / len(factories)) * 100.0

    def _get_critical_factory(self, factories):
        max_s = -1
        crit = None
        for f in factories:
            if f["fault"]["severity"] > max_s:
                max_s = f["fault"]["severity"]
                crit = f["factory_id"]
        return crit if max_s > 0 else None

    def stop(self):
        """Stop the engine."""
        self.registry.stop_all()
        self.bus.shutdown()
