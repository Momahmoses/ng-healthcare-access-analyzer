# 🏥 Nigeria Healthcare Access Gap Analyzer

Geospatial platform for identifying underserved communities across Nigeria's 36 states, measuring facility density, travel-time catchments, and healthcare coverage gaps using **GIS**, **PySpark**, **Azure**, and **Streamlit**.

## Problem Statement
Over 50% of Nigerians live more than 5km from a health facility. Rural states in the North-East and North-West have fewer than 0.2 doctors per 1,000 people — far below WHO's 1:1,000 benchmark. This tool helps health planners prioritize facility construction and resource allocation.

## Tech Stack
| Layer | Technology |
|---|---|
| Geospatial | GeoPandas, Shapely, Folium |
| Big Data | PySpark on Azure Databricks |
| Cloud | Azure Blob Storage, Azure Health Data Services |
| Dashboard | Streamlit + Plotly |

## Project Structure
```
ng-healthcare-access-analyzer/
├── app.py                        # Streamlit dashboard
├── pipeline/spark_pipeline.py    # PySpark facility density & gap scoring
├── gis/spatial_analysis.py       # Catchment areas & nearest-facility distance
├── data/generate_data.py         # Synthetic facility and population data
├── azure/azure_config.py         # Azure Blob & Databricks helpers
└── requirements.txt
```

## Quick Start
```bash
pip install -r requirements.txt
python data/generate_data.py
streamlit run app.py
```

## Dashboard Features
- Interactive facility map with type-coded markers and state gap overlays
- KPI cards: active facilities, underserved states, avg travel time
- Gap score bar chart (worst to best coverage)
- Facility type donut chart
- Coverage vs population scatter by geopolitical zone
- Priority tier ranking table with WHO benchmark comparisons

## Data Sources (Production)
- **FMOH** — Federal Ministry of Health facility registry
- **NBS** — Population and housing census
- **WHO SARA** — Service availability and readiness assessment
- **OpenStreetMap Nigeria** — Road network for travel-time calculation
