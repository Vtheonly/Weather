"""
Data definitions for Algeria Renewable Energy Forecasting App.
Contains regional data and energy project details.
"""

# Algeria's main regions with their geographic coordinates and energy characteristics
ALGERIA_REGIONS = {
    "Adrar": {
        "lat": 27.8742, "lon": -0.2939,
        "area_km2": 443698,  # Largest wilaya
        "solar_potential": 0.95,  # Very high (Sahara region)
        "wind_potential": 0.92,
        "population_density": 1.5,  # per km2
        "existing_solar_mw": 150,
        "existing_wind_mw": 50,
        "description": "Saharan region with exceptional solar and wind resources"
    },
    "Tamanrasset": {
        "lat": 22.7850, "lon": 5.5228,
        "area_km2": 556200,
        "solar_potential": 0.98,  # Extremely high
        "wind_potential": 0.70,
        "population_density": 0.3,
        "existing_solar_mw": 80,
        "existing_wind_mw": 10,
        "description": "Hoggar Mountains region, highest solar irradiation"
    },
    "Bechar": {
        "lat": 31.6250, "lon": -2.2167,
        "area_km2": 161400,
        "solar_potential": 0.92,
        "wind_potential": 0.85,
        "population_density": 1.7,
        "existing_solar_mw": 60,
        "existing_wind_mw": 30,
        "description": "Saoura region, excellent for both solar and wind"
    },
    "Ghardaia": {
        "lat": 32.4917, "lon": 3.6744,
        "area_km2": 86105,
        "solar_potential": 0.90,
        "wind_potential": 0.75,
        "population_density": 4.5,
        "existing_solar_mw": 100,
        "existing_wind_mw": 0,
        "description": "M'zab Valley, major solar research hub"
    },
    "El Oued": {
        "lat": 33.3500, "lon": 6.8667,
        "area_km2": 54573,
        "solar_potential": 0.88,
        "wind_potential": 0.70,
        "population_density": 12.0,
        "existing_solar_mw": 110,
        "existing_wind_mw": 0,
        "description": "Souf region, high solar potential and grid connectivity"
    },
    "Oran": {
        "lat": 35.6969, "lon": -0.6331,
        "area_km2": 2114,
        "solar_potential": 0.75,
        "wind_potential": 0.80,  # Coastal wind
        "population_density": 700.0,
        "existing_solar_mw": 20,
        "existing_wind_mw": 10,
        "description": "Major coastal city, good wind potential"
    },
    "Algiers": {
        "lat": 36.7528, "lon": 3.0420,
        "area_km2": 1190,
        "solar_potential": 0.70,
        "wind_potential": 0.65,
        "population_density": 2500.0,
        "existing_solar_mw": 10,
        "existing_wind_mw": 0,
        "description": "Capital region, limited space but high demand"
    },
    "Hassi R'Mel": {
        "lat": 32.9333, "lon": 3.2500,
        "area_km2": 5000,  # Approximate zone
        "solar_potential": 0.91,
        "wind_potential": 0.82,
        "population_density": 8.5,
        "existing_solar_mw": 120,
        "existing_wind_mw": 35,
        "description": "Northern Sahara transition zone"
    },
    "Ouargla": {
        "lat": 31.9500, "lon": 5.3333,
        "area_km2": 211980,
        "solar_potential": 0.92,
        "wind_potential": 0.78,
        "population_density": 4.2,
        "existing_solar_mw": 90,
        "existing_wind_mw": 25,
        "description": "Oil rich region diversifying into renewables"
    },
    "Tindouf": {
        "lat": 27.6711, "lon": -8.1474,
        "area_km2": 159000,
        "solar_potential": 0.93,
        "wind_potential": 0.88,
        "population_density": 0.3,
        "existing_solar_mw": 25,
        "existing_wind_mw": 15,
        "description": "Westernmost region with high potential"
    },
    "Illizi": {
        "lat": 26.4833, "lon": 8.4667,
        "area_km2": 285000,
        "solar_potential": 0.94,
        "wind_potential": 0.70,
        "population_density": 0.1,
        "existing_solar_mw": 20,
        "existing_wind_mw": 5,
        "description": "Southeastern Sahara, high development potential"
    },
    "Djanet": {
        "lat": 24.5500, "lon": 9.4833,
        "area_km2": 86000,
        "solar_potential": 0.95,
        "wind_potential": 0.65,
        "population_density": 0.1,
        "existing_solar_mw": 15,
        "existing_wind_mw": 3,
        "description": "Tassili n'Ajjer region"
    },
    "Hassi Messaoud": {
        "lat": 31.6833, "lon": 6.1500,
        "area_km2": 7000,  # Approximate
        "solar_potential": 0.91,
        "wind_potential": 0.75,
        "population_density": 15.0,
        "existing_solar_mw": 200,
        "existing_wind_mw": 60,
        "description": "Oil hub with major energy infrastructure"
    },
    "Laghouat": {
        "lat": 33.8000, "lon": 2.8833,
        "area_km2": 25487,
        "solar_potential": 0.85,
        "wind_potential": 0.75,
        "population_density": 18.0,
        "existing_solar_mw": 60,
        "existing_wind_mw": 20,
        "description": "Steppe region with good renewable potential"
    },
    "Biskra": {
        "lat": 34.8500, "lon": 5.7333,
        "area_km2": 20786,
        "solar_potential": 0.83,
        "wind_potential": 0.68,
        "population_density": 32.0,
        "existing_solar_mw": 80,
        "existing_wind_mw": 25,
        "description": "Gateway to Sahara, growing solar capacity"
    },
    "Touggourt": {
        "lat": 33.1000, "lon": 6.0500,
        "area_km2": 21080,
        "solar_potential": 0.87,
        "wind_potential": 0.73,
        "population_density": 25.0,
        "existing_solar_mw": 45,
        "existing_wind_mw": 12,
        "description": "Palm region with agricultural energy needs"
    },
    "El Meniaa": {
        "lat": 30.5833, "lon": 2.8833,
        "area_km2": 62500,
        "solar_potential": 0.88,
        "wind_potential": 0.82,
        "population_density": 3.0,
        "existing_solar_mw": 35,
        "existing_wind_mw": 18,
        "description": "Central Saharan gateway"
    },
    "Timimoun": {
        "lat": 29.2500, "lon": 0.2500,
        "area_km2": 109000,
        "solar_potential": 0.94,
        "wind_potential": 0.86,
        "population_density": 1.0,
        "existing_solar_mw": 25,
        "existing_wind_mw": 15,
        "description": "Grand Erg Occidental region"
    },
    "Beni Abbas": {
        "lat": 30.1333, "lon": -2.4667,
        "area_km2": 95000,
        "solar_potential": 0.91,
        "wind_potential": 0.84,
        "population_density": 1.2,
        "existing_solar_mw": 20,
        "existing_wind_mw": 12,
        "description": "Saoura valley region"
    },
    "In Salah": {
        "lat": 27.2000, "lon": 2.4833,
        "area_km2": 135000,
        "solar_potential": 0.96,
        "wind_potential": 0.90,
        "population_density": 0.4,
        "existing_solar_mw": 40,
        "existing_wind_mw": 30,
        "description": "Central Sahara with major solar projects"
    },
    "In Guezzam": {
        "lat": 19.5667, "lon": 5.7500,
        "area_km2": 86000,
        "solar_potential": 0.98,
        "wind_potential": 0.55,
        "population_density": 0.1,
        "existing_solar_mw": 10,
        "existing_wind_mw": 2,
        "description": "Southernmost Algeria, extreme solar potential"
    },
    "Bordj Badji Mokhtar": {
        "lat": 21.3333, "lon": 4.9167,
        "area_km2": 120000,
        "solar_potential": 0.97,
        "wind_potential": 0.60,
        "population_density": 0.1,
        "existing_solar_mw": 8,
        "existing_wind_mw": 2,
        "description": "Deep south Saharan region"
    },
    "Mengoub": {
        "lat": 30.2833, "lon": 6.8000,
        "area_km2": 85000,
        "solar_potential": 0.89,
        "wind_potential": 0.76,
        "population_density": 0.8,
        "existing_solar_mw": 12,
        "existing_wind_mw": 8,
        "description": "Eastern Saharan region"
    }
}

# Major existing and planned renewable energy projects
ENERGY_PROJECTS = [
    {
        "name": "Adrar Solar Park",
        "lat": 27.8742, "lon": -0.2939,
        "type": "solar",
        "capacity_mw": 150,
        "status": "operational",
        "year": 2020
    },
    {
        "name": "Tafouk 1 Solar Complex",
        "lat": 31.9500, "lon": 5.3333,
        "type": "solar",
        "capacity_mw": 450,
        "status": "planned",
        "year": 2025
    },
    {
        "name": "Hassi R'Mel Hybrid",
        "lat": 32.9333, "lon": 3.2500,
        "type": "hybrid",
        "capacity_mw": 350,
        "status": "operational",
        "year": 2018
    },
    {
        "name": "Kaberten Wind Farm",
        "lat": 31.6250, "lon": -2.2167,
        "type": "wind",
        "capacity_mw": 40,
        "status": "operational",
        "year": 2019
    },
    {
        "name": "Tamanrasset Solar",
        "lat": 22.7850, "lon": 5.5228,
        "type": "solar",
        "capacity_mw": 80,
        "status": "operational",
        "year": 2021
    },
    {
        "name": "Bechar Wind Corridor",
        "lat": 31.6250, "lon": -2.2167,
        "type": "wind",
        "capacity_mw": 100,
        "status": "construction",
        "year": 2024
    },
    {
        "name": "Ghardaia Solar Cluster",
        "lat": 32.4917, "lon": 3.6744,
        "type": "solar",
        "capacity_mw": 120,
        "status": "operational",
        "year": 2022
    },
    {
        "name": "In Salah Mega Solar",
        "lat": 27.2000, "lon": 2.4833,
        "type": "solar",
        "capacity_mw": 500,
        "status": "planned",
        "year": 2026
    },
    {
        "name": "Hassi Messaoud Energy Hub",
        "lat": 31.6833, "lon": 6.1500,
        "type": "hybrid",
        "capacity_mw": 260,
        "status": "operational",
        "year": 2021
    },
    {
        "name": "Tindouf Solar-Wind Hybrid",
        "lat": 27.6706, "lon": -8.1472,
        "type": "hybrid",
        "capacity_mw": 40,
        "status": "construction",
        "year": 2024
    },
    {
        "name": "El Oued Solar Array",
        "lat": 33.3500, "lon": 6.8667,
        "type": "solar",
        "capacity_mw": 70,
        "status": "operational",
        "year": 2020
    },
    {
        "name": "Timimoun Integrated Solar",
        "lat": 29.2500, "lon": 0.2500,
        "type": "solar",
        "capacity_mw": 25,
        "status": "operational",
        "year": 2022
    }
]

# Factory definitions per region for the Fault Detection system
# Each factory has a battery energy storage system
REGION_FACTORIES = {
    "Adrar": [
        {"name": "Adrar Solar Plant A", "type": "solar", "capacity_kw": 75000, "battery_capacity_kwh": 50000, "initial_soc": 0.6},
        {"name": "Adrar Solar Plant B", "type": "solar", "capacity_kw": 75000, "battery_capacity_kwh": 45000, "initial_soc": 0.55},
        {"name": "Adrar Wind Farm", "type": "wind", "capacity_kw": 50000, "battery_capacity_kwh": 35000, "initial_soc": 0.5},
    ],
    "Tamanrasset": [
        {"name": "Tamanrasset Solar Alpha", "type": "solar", "capacity_kw": 40000, "battery_capacity_kwh": 30000, "initial_soc": 0.65},
        {"name": "Tamanrasset Solar Beta", "type": "solar", "capacity_kw": 40000, "battery_capacity_kwh": 25000, "initial_soc": 0.5},
    ],
    "Bechar": [
        {"name": "Bechar Solar Station", "type": "solar", "capacity_kw": 30000, "battery_capacity_kwh": 20000, "initial_soc": 0.5},
        {"name": "Kaberten Wind Farm", "type": "wind", "capacity_kw": 40000, "battery_capacity_kwh": 30000, "initial_soc": 0.45},
        {"name": "Bechar Hybrid Unit", "type": "solar", "capacity_kw": 30000, "battery_capacity_kwh": 22000, "initial_soc": 0.55},
    ],
    "Ghardaia": [
        {"name": "Ghardaia Solar Cluster 1", "type": "solar", "capacity_kw": 60000, "battery_capacity_kwh": 40000, "initial_soc": 0.6},
        {"name": "Ghardaia Solar Cluster 2", "type": "solar", "capacity_kw": 60000, "battery_capacity_kwh": 38000, "initial_soc": 0.55},
    ],
    "El Oued": [
        {"name": "El Oued Solar Array", "type": "solar", "capacity_kw": 55000, "battery_capacity_kwh": 35000, "initial_soc": 0.5},
        {"name": "El Oued Solar Field B", "type": "solar", "capacity_kw": 55000, "battery_capacity_kwh": 32000, "initial_soc": 0.6},
    ],
    "Oran": [
        {"name": "Oran Coastal Wind", "type": "wind", "capacity_kw": 10000, "battery_capacity_kwh": 8000, "initial_soc": 0.5},
        {"name": "Oran Solar Rooftop", "type": "solar", "capacity_kw": 20000, "battery_capacity_kwh": 12000, "initial_soc": 0.55},
    ],
    "Algiers": [
        {"name": "Algiers Urban Solar", "type": "solar", "capacity_kw": 10000, "battery_capacity_kwh": 8000, "initial_soc": 0.5},
    ],
    "Hassi R'Mel": [
        {"name": "Hassi R'Mel Hybrid Solar", "type": "solar", "capacity_kw": 60000, "battery_capacity_kwh": 45000, "initial_soc": 0.6},
        {"name": "Hassi R'Mel Wind Station", "type": "wind", "capacity_kw": 35000, "battery_capacity_kwh": 25000, "initial_soc": 0.5},
        {"name": "Hassi R'Mel CSP Unit", "type": "solar", "capacity_kw": 60000, "battery_capacity_kwh": 50000, "initial_soc": 0.55},
    ],
    "Ouargla": [
        {"name": "Ouargla Solar Farm", "type": "solar", "capacity_kw": 45000, "battery_capacity_kwh": 30000, "initial_soc": 0.55},
        {"name": "Ouargla Wind Turbines", "type": "wind", "capacity_kw": 25000, "battery_capacity_kwh": 18000, "initial_soc": 0.5},
    ],
    "Tindouf": [
        {"name": "Tindouf Solar-Wind Hybrid", "type": "solar", "capacity_kw": 25000, "battery_capacity_kwh": 18000, "initial_soc": 0.5},
        {"name": "Tindouf Wind Array", "type": "wind", "capacity_kw": 15000, "battery_capacity_kwh": 12000, "initial_soc": 0.45},
    ],
    "Illizi": [
        {"name": "Illizi Solar Station", "type": "solar", "capacity_kw": 20000, "battery_capacity_kwh": 15000, "initial_soc": 0.6},
    ],
    "Djanet": [
        {"name": "Djanet Solar Oasis", "type": "solar", "capacity_kw": 15000, "battery_capacity_kwh": 10000, "initial_soc": 0.55},
    ],
    "Hassi Messaoud": [
        {"name": "HMD Energy Hub Solar", "type": "solar", "capacity_kw": 100000, "battery_capacity_kwh": 80000, "initial_soc": 0.6},
        {"name": "HMD Energy Hub Wind", "type": "wind", "capacity_kw": 60000, "battery_capacity_kwh": 45000, "initial_soc": 0.5},
        {"name": "HMD Industrial Solar", "type": "solar", "capacity_kw": 100000, "battery_capacity_kwh": 70000, "initial_soc": 0.55},
    ],
    "Laghouat": [
        {"name": "Laghouat Solar Park", "type": "solar", "capacity_kw": 30000, "battery_capacity_kwh": 20000, "initial_soc": 0.5},
        {"name": "Laghouat Wind Farm", "type": "wind", "capacity_kw": 20000, "battery_capacity_kwh": 15000, "initial_soc": 0.5},
    ],
    "Biskra": [
        {"name": "Biskra Solar Gateway", "type": "solar", "capacity_kw": 40000, "battery_capacity_kwh": 28000, "initial_soc": 0.55},
        {"name": "Biskra Wind Connect", "type": "wind", "capacity_kw": 25000, "battery_capacity_kwh": 18000, "initial_soc": 0.5},
    ],
    "Touggourt": [
        {"name": "Touggourt Solar Array", "type": "solar", "capacity_kw": 22000, "battery_capacity_kwh": 16000, "initial_soc": 0.5},
        {"name": "Touggourt Wind Unit", "type": "wind", "capacity_kw": 12000, "battery_capacity_kwh": 9000, "initial_soc": 0.45},
    ],
    "El Meniaa": [
        {"name": "El Meniaa Solar Field", "type": "solar", "capacity_kw": 17500, "battery_capacity_kwh": 12000, "initial_soc": 0.5},
        {"name": "El Meniaa Wind Station", "type": "wind", "capacity_kw": 18000, "battery_capacity_kwh": 13000, "initial_soc": 0.5},
    ],
    "Timimoun": [
        {"name": "Timimoun Integrated Solar", "type": "solar", "capacity_kw": 12500, "battery_capacity_kwh": 9000, "initial_soc": 0.55},
        {"name": "Timimoun Wind Array", "type": "wind", "capacity_kw": 15000, "battery_capacity_kwh": 11000, "initial_soc": 0.5},
    ],
    "Beni Abbas": [
        {"name": "Beni Abbas Solar", "type": "solar", "capacity_kw": 10000, "battery_capacity_kwh": 7000, "initial_soc": 0.5},
        {"name": "Beni Abbas Wind", "type": "wind", "capacity_kw": 12000, "battery_capacity_kwh": 8500, "initial_soc": 0.5},
    ],
    "In Salah": [
        {"name": "In Salah Mega Solar A", "type": "solar", "capacity_kw": 20000, "battery_capacity_kwh": 15000, "initial_soc": 0.6},
        {"name": "In Salah Mega Solar B", "type": "solar", "capacity_kw": 20000, "battery_capacity_kwh": 14000, "initial_soc": 0.55},
        {"name": "In Salah Wind Farm", "type": "wind", "capacity_kw": 30000, "battery_capacity_kwh": 22000, "initial_soc": 0.5},
    ],
    "In Guezzam": [
        {"name": "In Guezzam Solar", "type": "solar", "capacity_kw": 5000, "battery_capacity_kwh": 4000, "initial_soc": 0.5},
    ],
    "Bordj Badji Mokhtar": [
        {"name": "BBM Solar Station", "type": "solar", "capacity_kw": 4000, "battery_capacity_kwh": 3000, "initial_soc": 0.5},
    ],
    "Mengoub": [
        {"name": "Mengoub Solar Field", "type": "solar", "capacity_kw": 6000, "battery_capacity_kwh": 4500, "initial_soc": 0.5},
        {"name": "Mengoub Wind Unit", "type": "wind", "capacity_kw": 8000, "battery_capacity_kwh": 6000, "initial_soc": 0.5},
    ],
}
