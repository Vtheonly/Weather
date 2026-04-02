# Algeria Renewable Energy Forecasting & Microgrid Dashboard

A unified platform combining an interactive Streamlit UI with a high-performance FastAPI back-end to visualize, forecast, and detect faults in renewable energy systems (solar and wind) across Algeria. The platform leverages heavy machine learning models, physics-based simulations, and a C++ Wavelet Transform engine for real-time DSP.

## 🚀 How to Launch

The entire application relies on a microservice architecture and is designed to be run **exclusively through Docker Compose**. 

> [!WARNING]  
> **First-Time Build Wait Time (~20+ mins):**  
> Because the backend `api` container relies on enormous machine learning frameworks (`tensorflow`, `torch`, `xgboost` totaling over 2.5 GB), your *very first* run of `docker compose build` will take a **long time to download dependencies**. This is completely normal!
> 
> **Do not cancel the build!** Once the heavy libraries are downloaded, Docker caches them. All your subsequent builds will finish in seconds.

### 1. Build and Run the Application

From the root project directory, execute:

```bash
docker compose up -d --build
```

### 2. Access the Services

Once the containers are successfully running, open your web browser to the following endpoints:

* **Frontend Dashboard (Streamlit)**: [http://localhost:8501](http://localhost:8501)
* **Backend API (FastAPI)**: [http://localhost:8000/docs](http://localhost:8000/docs) (Interactive Swagger UI)

### 3. Viewing Logs

If you want to monitor the system running or check for setup errors:

```bash
# View logs for both containers
docker compose logs -f
```

## 🏗️ Architecture

1. **Frontend (`ui/`)**: A Streamlit interface for map visualization, data exploration, and digital twin monitoring.
2. **Backend API (`api/`)**: A FastAPI engine hosting inference pipelines, the `dc_microgrid_dwt` simulation backend, and bridging calls to the backend logic.
3. **Core ML / DSP Code**:
    - **`pklh5_NN_engine/`**: Houses multiple pre-trained Deep Learning files and transformers (`.h5`, `.pkl`, `.pt`).
    - **C++ Builder**: The backend dynamically builds optimized C++ pybind11 modules upon initialization (via the Docker `builder` stage).

## ✨ Features

- **Interactive Map**: Folium-based map centered on Algeria with multiple energy prospect layers.
- **Microgrid Fault Detection**: Advanced real-time analysis using Discrete Wavelet Transforms.
- **Solar & Wind Forecasting**: Deep neural network and tree-based forecasting for various energy production zones.
- **Unified Pipeline**: Connects site-specific environmental conditions directly into the digital twin circuit simulations.
