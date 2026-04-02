# Algeria Renewable Energy Factories API

REST API for the Algeria Renewable Energy Fault Detection System, designed for Docker integration.

## Features

- **City & Factory Management**: List and query cities with their factory configurations
- **Fault Detection**: Real-time wavelet-based anomaly detection for factory power monitoring
- **Battery Simulation**: Battery state-of-charge, voltage, current, and temperature simulation
- **Fault Injection**: Controlled fault injection for testing and validation
- **Docker Ready**: Designed for containerized deployment

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python api/main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t factories-api .
docker run -p 8000:8000 factories-api
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | API health check |

### Cities & Factories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cities` | List all cities/regions |
| GET | `/api/v1/cities/{region}` | Get city details |
| GET | `/api/v1/factories/{region}` | List factories in a region |

### Fault Detection Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/detector/{region}/tick` | Advance simulation |
| POST | `/api/v1/detector/{region}/analyze` | Run fault analysis |
| GET | `/api/v1/detector/{region}/state` | Get detector state |
| POST | `/api/v1/detector/{region}/inject-fault` | Inject test fault |
| POST | `/api/v1/detector/{region}/clear-faults` | Clear all faults |
| DELETE | `/api/v1/detector/{region}` | Reset detector |

## Usage Examples

### List all cities

```bash
curl http://localhost:8000/api/v1/cities
```

### Get factories in Adrar region

```bash
curl http://localhost:8000/api/v1/factories/Adrar
```

### Run fault analysis on a region

```bash
curl -X POST http://localhost:8000/api/v1/detector/Adrar/analyze
```

### Inject a battery fault

```bash
curl -X POST http://localhost:8000/api/v1/detector/Adrar/inject-fault \
  -H "Content-Type: application/json" \
  -d '{"factory_id": "Adrar Solar Plant A", "fault_type": "battery", "severity": 0.7}'
```

### Advance simulation by 10 ticks

```bash
curl -X POST http://localhost:8000/api/v1/detector/Adrar/tick \
  -H "Content-Type: application/json" \
  -d '{"iterations": 10, "dt_seconds": 1.0}'
```

## Fault Classes

| Class | Description |
|-------|-------------|
| `NORMAL` | All systems operating within parameters |
| `NOISE` | High-frequency sensor noise detected |
| `DISTURBANCE` | Transient power fluctuation |
| `BATTERY_FAULT` | Battery system anomaly |
| `LINE_FAULT` | Power line/connection fault |
| `DANGEROUS` | Critical condition requiring immediate action |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONPATH` | `/app` | Python path |
| `LOG_LEVEL` | `info` | Logging level |
| `API_HOST` | `0.0.0.0` | API host |
| `API_PORT` | `8000` | API port |

### Resource Limits (Docker)

- **CPU**: 2.0 cores limit, 0.5 cores reserved
- **Memory**: 2GB limit, 512MB reserved

## Architecture

```
api/
├── __init__.py          # Module exports
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── routes.py            # API endpoints
└── README.md            # This file

core/
├── fault_detection/     # Fault detection engine
│   ├── battery.py       # Battery simulation
│   ├── fault_detector.py # Fault orchestrator
│   └── wavelet_engine.py # Wavelet analysis
└── ...

config/
├── data.py              # Regional data & factory configs
└── settings.py          # App settings
```

## Integration with Docker

This API is designed to be deployed as a Docker container and can communicate with other services:

1. **Standalone**: Run the API directly with `docker-compose up`
2. **Microservice**: Integrate with other containers via Docker network
3. **External Engine**: Forward requests from another engine inside Docker

### Example Docker Network Communication

```yaml
# docker-compose.yml
services:
  factories-api:
    build: .
    networks:
      - energy-network
  
  your-engine:
    image: your-engine-image
    networks:
      - energy-network
    environment:
      - FACTORIES_API_URL=http://factories-api:8000

networks:
  energy-network:
    driver: bridge
```

Then in your engine, call the API:
```python
import requests
response = requests.get("http://factories-api:8000/api/v1/cities")
```

## Testing

```bash
# Health check
curl http://localhost:8000/api/v1/health

# List regions
curl http://localhost:8000/api/v1/cities

# Run full analysis
curl -X POST http://localhost:8000/api/v1/detector/Adrar/analyze
```

## License

Part of the Algeria Renewable Energy Forecast Application.