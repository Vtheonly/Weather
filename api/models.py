"""
Pydantic models for the Factories API.
Defines request/response schemas for the REST API.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum


class FaultClass(str, Enum):
    """Fault classification categories."""
    NORMAL = "NORMAL"
    NOISE = "NOISE"
    DISTURBANCE = "DISTURBANCE"
    BATTERY_FAULT = "BATTERY_FAULT"
    LINE_FAULT = "LINE_FAULT"
    DANGEROUS = "DANGEROUS"
    INITIALIZING = "INITIALIZING"


class FactoryType(str, Enum):
    """Factory energy type."""
    SOLAR = "solar"
    WIND = "wind"


class FactoryConfig(BaseModel):
    """Factory configuration model."""
    name: str = Field(..., description="Factory unique identifier")
    type: FactoryType = Field(..., description="Factory energy type")
    capacity_kw: float = Field(..., description="Factory capacity in kW")
    battery_capacity_kwh: float = Field(..., description="Battery capacity in kWh")
    initial_soc: float = Field(default=0.5, ge=0.0, le=1.0, description="Initial state of charge")


class BatteryState(BaseModel):
    """Battery state model."""
    factory_id: str
    soc: float = Field(..., description="State of charge (0-1)")
    soc_pct: float = Field(..., description="State of charge percentage")
    voltage: float = Field(..., description="Battery voltage in V")
    current: float = Field(..., description="Battery current in A")
    temperature: float = Field(..., description="Battery temperature in °C")
    energy_in_kwh: float = Field(..., description="Total energy charged in kWh")
    energy_out_kwh: float = Field(..., description="Total energy discharged in kWh")
    peak_charge_kw: float = Field(..., description="Peak charge power in kW")
    peak_discharge_kw: float = Field(..., description="Peak discharge power in kWh")


class FaultResult(BaseModel):
    """Fault detection result model."""
    factory_id: str
    fault_class: FaultClass
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: int = Field(..., ge=0, le=5)
    explanation: str
    power_anomaly: bool = False
    voltage_anomaly: bool = False
    current_anomaly: bool = False
    battery_anomaly: bool = False


class WaveletFeatures(BaseModel):
    """Wavelet analysis features."""
    energies: List[float]
    energy_ratios: List[float]
    kurtosis: List[float]
    total_energy: float
    high_freq_ratio: float
    low_freq_ratio: float


class FactoryState(BaseModel):
    """Complete factory state model."""
    factory_id: str
    type: FactoryType
    capacity_kw: float
    battery: BatteryState
    power_history: List[float] = Field(default_factory=list)
    voltage_history: List[float] = Field(default_factory=list)
    soc_history: List[float] = Field(default_factory=list)
    fault: FaultResult
    wavelet_features: Optional[WaveletFeatures] = None


class RegionSummary(BaseModel):
    """Region fault detection summary."""
    total_factories: int
    fault_counts: Dict[FaultClass, int]
    health_score: float = Field(..., ge=0.0, le=100.0)
    max_severity: int = Field(..., ge=0, le=5)
    critical_factory: Optional[str] = None


class DashboardState(BaseModel):
    """Complete dashboard state model."""
    region: str
    tick_count: int
    uptime_seconds: float
    factories: List[FactoryState]
    summary: RegionSummary


class InjectFaultRequest(BaseModel):
    """Request model for fault injection."""
    factory_id: str = Field(..., description="Target factory ID")
    fault_type: str = Field(..., pattern="^(battery|line)$", description="Fault type: battery or line")
    severity: float = Field(default=0.5, ge=0.1, le=1.0, description="Fault severity (0.1-1.0)")


class TickRequest(BaseModel):
    """Request model for simulation tick."""
    dt_seconds: float = Field(default=1.0, gt=0.0, description="Time step in seconds")
    iterations: int = Field(default=1, ge=1, le=100, description="Number of tick iterations")


class AnalyzeRequest(BaseModel):
    """Request model for fault analysis."""
    region: str = Field(..., description="Region name to analyze")


class RegionInfo(BaseModel):
    """Region information model."""
    name: str
    lat: float
    lon: float
    area_km2: float
    solar_potential: float
    wind_potential: float
    factories: List[FactoryConfig]


class FactoryListResponse(BaseModel):
    """Response model for factory listing."""
    region: str
    factories: List[FactoryConfig]
    total_count: int


class CityListResponse(BaseModel):
    """Response model for city listing."""
    cities: List[RegionInfo]
    total_count: int


class HealthResponse(BaseModel):
    """API health check response."""
    status: str = "ok"
    version: str
    regions_loaded: int
    active_detectors: int


# ─── AI Prediction Models ───────────────────────────────────────────────────

class SolarDataPoint(BaseModel):
    """Weather features for a single solar prediction point."""
    ghi: float
    temp: float
    humidity: float
    wind_speed: float
    hour: int

class SolarPredictRequest(BaseModel):
    """Request model for Solar AI Prediction."""
    points: List[SolarDataPoint]
    recent_residuals: Optional[List[float]] = Field(None, description="Last 24 hourly residuals for LSTM correction")

class SolarPredictResponse(BaseModel):
    """Response model for Solar AI Prediction."""
    predictions_kw: List[float]
    sigmas: List[float]
    model_version: str = "hybrid_v1"

class WindDataPoint(BaseModel):
    """Single telemetry point for Wind AI."""
    Wspd: float
    Wdir: float
    Etmp: float
    Itmp: float
    Ndir: float
    Pab1: float
    Pab2: float
    Pab3: float
    Prtv: float
    Patv: float

class WindPredictRequest(BaseModel):
    """Request model for Wind AI Prediction."""
    history: List[WindDataPoint] = Field(..., min_items=144, description="Last 24 hours of 10-min telemetry")

class WindPredictResponse(BaseModel):
    """Response model for Wind AI Prediction."""
    forecast: List[float]
    horizon_hours: int = 48
    model_version: str = "transformer_v1"