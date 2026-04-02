"""
Factories API Main Application.
FastAPI server exposing fault detection system for Docker integration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import router

# Create FastAPI application
app = FastAPI(
    title="Algeria Renewable Energy Factories API",
    description="""
    REST API for the Algeria Renewable Energy Fault Detection System.
    
    ## Features
    
    - **City & Factory Management**: List and query cities with their factory configurations
    - **Fault Detection**: Real-time wavelet-based anomaly detection for factory power monitoring
    - **Battery Simulation**: Battery state-of-charge, voltage, current, and temperature simulation
    - **Fault Injection**: Controlled fault injection for testing and validation
    - **Docker Ready**: Designed for containerized deployment
    
    ## Endpoints
    
    ### Health & Status
    - `GET /api/v1/health` - API health check
    
    ### Cities & Factories
    - `GET /api/v1/cities` - List all cities/regions
    - `GET /api/v1/cities/{region}` - Get city details
    - `GET /api/v1/factories/{region}` - List factories in a region
    
    ### Fault Detection Engine
    - `POST /api/v1/detector/{region}/tick` - Advance simulation
    - `POST /api/v1/detector/{region}/analyze` - Run fault analysis
    - `GET /api/v1/detector/{region}/state` - Get detector state
    - `POST /api/v1/detector/{region}/inject-fault` - Inject test fault
    - `POST /api/v1/detector/{region}/clear-faults` - Clear all faults
    - `DELETE /api/v1/detector/{region}` - Reset detector
    
    ## Fault Classes
    
    - `NORMAL` - All systems operating within parameters
    - `NOISE` - High-frequency sensor noise detected
    - `DISTURBANCE` - Transient power fluctuation
    - `BATTERY_FAULT` - Battery system anomaly
    - `LINE_FAULT` - Power line/connection fault
    - `DANGEROUS` - Critical condition requiring immediate action
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS for cross-origin requests (Docker integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Algeria Renewable Energy Factories API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "cities": "/api/v1/cities",
        "description": "Fault detection system for renewable energy factories"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


# Application entry point for direct execution
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )