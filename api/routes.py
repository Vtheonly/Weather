"""
API Routes for the Factories API.
Defines all REST endpoints for fault detection system.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional

from api.models import (
    FactoryConfig, FactoryType, DashboardState, InjectFaultRequest,
    TickRequest, AnalyzeRequest, RegionInfo, FactoryListResponse,
    CityListResponse, HealthResponse, FaultResult, FaultClass,
    SolarPredictRequest, SolarPredictResponse, WindPredictRequest, WindPredictResponse
)
from config.data import ALGERIA_REGIONS, REGION_FACTORIES
from api.engine_adapter import EngineAdapter

# AI Model Imports
from core.models.hybrid_wrapper import SolarAIHybridModel
from core.models.wind_wrapper import WindProductionEngine

router = APIRouter(prefix="/api/v1", tags=["factories"])

# Global engine adapter cache
_engines: Dict[str, EngineAdapter] = {}

# Global AI Model Instances (Lazy Loaded)
_solar_model = None
_wind_engine = None

def get_solar_model():
    """Lazily load Solar AI Model."""
    global _solar_model
    if _solar_model is None:
        _solar_model = SolarAIHybridModel()
    return _solar_model

def get_wind_engine():
    """Lazily load Wind AI Engine."""
    global _wind_engine
    if _wind_engine is None:
        _wind_engine = WindProductionEngine()
    return _wind_engine


def _get_engine(region: str) -> EngineAdapter:
    """Get or create engine adapter for a region."""
    if region not in _engines:
        if region not in REGION_FACTORIES:
            raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
        factories = REGION_FACTORIES[region]
        _engines[region] = EngineAdapter(region, factories)
    return _engines[region]


def _parse_factory_config(cfg: dict) -> FactoryConfig:
    """Parse factory config dict to FactoryConfig model."""
    return FactoryConfig(
        name=cfg['name'],
        type=FactoryType(cfg['type']),
        capacity_kw=cfg['capacity_kw'],
        battery_capacity_kwh=cfg['battery_capacity_kwh'],
        initial_soc=cfg.get('initial_soc', 0.5)
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """API health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        regions_loaded=len(REGION_FACTORIES),
        active_detectors=len(_engines)
    )


@router.get("/cities", response_model=CityListResponse)
async def list_cities():
    """
    List all available cities/regions with their factory configurations.
    
    Returns a list of all regions with their geographic data and factory setups.
    """
    cities = []
    
    for region_name, region_data in ALGERIA_REGIONS.items():
        factories_config = REGION_FACTORIES.get(region_name, [])
        
        factories = [_parse_factory_config(cfg) for cfg in factories_config]
        
        cities.append(RegionInfo(
            name=region_name,
            lat=region_data['lat'],
            lon=region_data['lon'],
            area_km2=region_data['area_km2'],
            solar_potential=region_data['solar_potential'],
            wind_potential=region_data['wind_potential'],
            factories=factories
        ))
    
    return CityListResponse(
        cities=cities,
        total_count=len(cities)
    )


@router.get("/cities/{region}", response_model=RegionInfo)
async def get_city(region: str):
    """
    Get detailed information about a specific city/region.
    
    Returns geographic data and factory configurations for the region.
    """
    if region not in ALGERIA_REGIONS:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    
    region_data = ALGERIA_REGIONS[region]
    factories_config = REGION_FACTORIES.get(region, [])
    factories = [_parse_factory_config(cfg) for cfg in factories_config]
    
    return RegionInfo(
        name=region,
        lat=region_data['lat'],
        lon=region_data['lon'],
        area_km2=region_data['area_km2'],
        solar_potential=region_data['solar_potential'],
        wind_potential=region_data['wind_potential'],
        factories=factories
    )


@router.get("/factories/{region}", response_model=FactoryListResponse)
async def list_factories(region: str):
    """
    List all factories in a specific region.
    
    Returns factory configurations for the specified region.
    """
    if region not in REGION_FACTORIES:
        raise HTTPException(status_code=404, detail=f"Region '{region}' not found")
    
    factories_config = REGION_FACTORIES[region]
    factories = [_parse_factory_config(cfg) for cfg in factories_config]
    
    return FactoryListResponse(
        region=region,
        factories=factories,
        total_count=len(factories)
    )


@router.post("/detector/{region}/tick", response_model=DashboardState)
async def tick_detector(region: str, request: TickRequest = TickRequest()):
    """
    Advance simulation for a region by one or more time steps.
    
    Returns complete dashboard state after the tick(s).
    """
    engine = _get_engine(region)
    
    # Run requested number of ticks
    engine.tick(iterations=request.iterations)
    
    # Analyze and return state (analyze is built-in to Adapter if needed, or we just get state)
    dashboard = engine.get_dashboard_state()
    
    return _convert_dashboard_state(dashboard)


@router.post("/detector/{region}/analyze", response_model=DashboardState)
async def analyze_region(region: str):
    """
    Run wavelet fault analysis on a region's factories.
    
    Returns complete dashboard state with fault classification results.
    """
    engine = _get_engine(region)
    # Analysis is usually handled by the agents in the engine automatically
    dashboard = engine.get_dashboard_state()
    
    return _convert_dashboard_state(dashboard)


@router.get("/detector/{region}/state", response_model=DashboardState)
async def get_detector_state(region: str):
    """
    Get current state of fault detector for a region.
    
    Returns current dashboard state without running new ticks.
    """
    engine = _get_engine(region)
    dashboard = engine.get_dashboard_state()
    
    return _convert_dashboard_state(dashboard)


@router.post("/detector/{region}/inject-fault")
async def inject_fault(region: str, request: InjectFaultRequest):
    """
    Inject a controlled fault into a specific factory for testing.
    
    Returns confirmation of fault injection.
    """
    engine = _get_engine(region)
    
    engine.inject_fault(request.factory_id, request.fault_type, request.severity)
    
    return {
        "status": "success",
        "message": f"Injected {request.fault_type} fault into {request.factory_id}",
        "factory_id": request.factory_id,
        "fault_type": request.fault_type,
        "severity": request.severity
    }


@router.get("/detector/{region}/fault")
async def get_fault_info(region: str):
    """
    Get detailed fault information for a region.
    """
    engine = _get_engine(region)
    dashboard = engine.get_dashboard_state()
    
    # Extract active fault info from summary or factories
    active = dashboard['summary']['max_severity'] > 0
    fault_type = "NORMAL"
    location = ""
    distance = 0.0
    
    if active:
        critical_fid = dashboard['summary']['critical_factory']
        for f in dashboard['factories']:
            if f['factory_id'] == critical_fid:
                fault_type = f['fault']['class']
                location = critical_fid
                distance = 10.0 # Default
                break
                
    return {
        "active": active,
        "type": fault_type,
        "location": location,
        "distance": distance
    }


@router.get("/detector/{region}/circuit")
async def get_circuit_info(region: str, node_id: Optional[str] = Query(None)):
    """
    Get circuit topology information for the digital twin.
    If node_id is provided, returns the internal circuit of that factory.
    """
    engine = _get_engine(region)
    return engine.get_topology(node_id=node_id)


@router.post("/detector/{region}/clear-faults")
async def clear_faults(region: str):
    """
    Clear all injected faults in a region.
    
    Returns confirmation of fault clearing.
    """
    engine = _get_engine(region)
    engine.clear_faults()
    
    return {
        "status": "success",
        "message": f"Cleared all faults in region '{region}'"
    }


@router.delete("/detector/{region}")
async def reset_detector(region: str):
    """
    Reset and remove fault detector for a region.
    
    Returns confirmation of detector reset.
    """
    if region in _engines:
        engine = _engines[region]
        engine.stop()
        del _engines[region]
        return {
            "status": "success",
            "message": f"Reset detector for region '{region}'"
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No active detector for region '{region}'"
        )


def _convert_dashboard_state(dashboard: dict) -> DashboardState:
    """Convert detector dashboard dict to DashboardState model."""
    from api.models import (
        BatteryState, FactoryState, RegionSummary, WaveletFeatures
    )
    
    # Convert fault counts to FaultClass enum
    fault_counts = {}
    for k, v in dashboard['summary']['fault_counts'].items():
        try:
            fault_counts[FaultClass(k)] = v
        except ValueError:
            fault_counts[FaultClass.INITIALIZING] = v
    
    # Convert factories
    factories = []
    for f in dashboard['factories']:
        # Battery state
        bat = BatteryState(
            factory_id=f['battery']['factory_id'],
            soc=f['battery']['soc'],
            soc_pct=f['battery']['soc_pct'],
            voltage=f['battery']['voltage'],
            current=f['battery']['current'],
            temperature=f['battery']['temperature'],
            energy_in_kwh=f['battery']['energy_in_kwh'],
            energy_out_kwh=f['battery']['energy_out_kwh'],
            peak_charge_kw=f['battery']['peak_charge_kw'],
            peak_discharge_kw=f['battery']['peak_discharge_kw']
        )
        
        # Fault result
        try:
            fault_class = FaultClass(f['fault']['class'])
        except ValueError:
            fault_class = FaultClass.INITIALIZING
        
        fault = FaultResult(
            factory_id=f['factory_id'],
            fault_class=fault_class,
            confidence=f['fault']['confidence'],
            severity=f['fault']['severity'],
            explanation=f['fault']['explanation'],
            power_anomaly=f['fault']['power_anomaly'],
            voltage_anomaly=f['fault']['voltage_anomaly'],
            current_anomaly=f['fault']['current_anomaly'],
            battery_anomaly=f['fault']['battery_anomaly']
        )
        
        # Wavelet features (optional)
        wavelet_features = None
        if f.get('wavelet_features'):
            wf = f['wavelet_features']
            wavelet_features = WaveletFeatures(
                energies=wf['energies'],
                energy_ratios=wf['energy_ratios'],
                kurtosis=wf['kurtosis'],
                total_energy=wf['total_energy'],
                high_freq_ratio=wf['high_freq_ratio'],
                low_freq_ratio=wf['low_freq_ratio']
            )
        
        # Factory state
        factory_state = FactoryState(
            factory_id=f['factory_id'],
            type=FactoryType(f['type']),
            capacity_kw=f['capacity_kw'],
            battery=bat,
            power_history=f['power_history'],
            voltage_history=f['voltage_history'],
            soc_history=f['soc_history'],
            fault=fault,
            wavelet_features=wavelet_features
        )
        factories.append(factory_state)
    
    # Region summary
    summary = RegionSummary(
        total_factories=dashboard['summary']['total_factories'],
        fault_counts=fault_counts,
        health_score=dashboard['summary']['health_score'],
        max_severity=dashboard['summary']['max_severity'],
        critical_factory=dashboard['summary']['critical_factory']
    )
    
    return DashboardState(
        region=dashboard['region'],
        tick_count=dashboard['tick_count'],
        uptime_seconds=dashboard['uptime_seconds'],
        factories=factories,
        summary=summary
    )


# ─── AI Prediction Routes ───────────────────────────────────────────────────

@router.post("/ai/solar/predict", response_model=SolarPredictResponse, tags=["ai"])
async def predict_solar(request: SolarPredictRequest):
    """
    Predict solar power output using the Hybrid AI model.
    """
    import numpy as np
    import pandas as pd
    
    model = get_solar_model()
    
    # Prepare features for XGBoost stage
    features_list = []
    for p in request.points:
        features_list.append({
            'ghi': p.ghi,
            'temp': p.temp,
            'humidity': p.humidity,
            'wind_speed': p.wind_speed,
            'hour_sin': np.sin(2 * np.pi * p.hour / 24),
            'hour_cos': np.cos(2 * np.pi * p.hour / 24)
        })
    
    features_df = pd.DataFrame(features_list)
    
    # Note: SolarAIHybridModel currently expects 1 residual set at a time? 
    # Let's check wrapper.predict again. 
    # Wrapper.predict(features_df, recent_residuals)
    
    # If points is a list, we might need to loop or the wrapper might handle it.
    # Current wrapper code:
    # steps_input = features_df[xgb_cols]
    # xgb_pred = self.xgb_model.predict(steps_input)[0]
    # It only returns ONE prediction [0].
    
    # So I will loop for now to fulfill the interface.
    predictions = []
    sigmas = []
    
    residuals = None
    if request.recent_residuals:
        residuals = np.array(request.recent_residuals).reshape(1, 24, 1)
        
    for i in range(len(features_df)):
        # Run point-by-point for simplicity given current wrapper design
        p, s = model.predict(features_df.iloc[[i]], residuals)
        predictions.append(float(p))
        sigmas.append(float(s))
        
    return SolarPredictResponse(
        predictions_kw=predictions,
        sigmas=sigmas
    )


@router.post("/ai/wind/predict", response_model=WindPredictResponse, tags=["ai"])
async def predict_wind(request: WindPredictRequest):
    """
    Generate a 48-hour wind power forecast using the Transformer model.
    """
    import pandas as pd
    
    engine = get_wind_engine()
    
    # Convert request data to DataFrame
    history_df = pd.DataFrame([p.dict() for p in request.history])
    
    # Run inference
    forecast = engine.predict_48h(history_df)
    
    if forecast is None:
        raise HTTPException(status_code=400, detail="Insufficient history or model failure")
        
    return WindPredictResponse(
        forecast=forecast.tolist()
    )