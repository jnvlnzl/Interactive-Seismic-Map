# config.py
import os
from datetime import datetime

# File path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

PROVINCES_GEOJSON = os.path.join(DATA_DIR, "ph_provinces.geojson")
FAULTS_GEOJSON = os.path.join(DATA_DIR, "gem_active_faults.geojson")
MAGNITUDE_CSV = os.path.join(DATA_DIR, "[POP] FINAL_merged_earthquake_data.csv")

# CSS
CSS_FILE_RELATIVE = 'style.css' 
CSS_FILE = os.path.join(ASSETS_DIR, CSS_FILE_RELATIVE) 

# Map settings
DEFAULT_CENTER = {"lat": 12.8797, "lon": 121.7740}
DEFAULT_ZOOM = 4.5

# Magnitude slider settings
MAGNITUDE_RANGES = [
    None, (1.0, 1.9), (2.0, 2.9), (3.0, 3.9), (4.0, 4.9),
    (5.0, 5.9), (6.0, 6.9), (7.0, 7.9), (8.0, 8.9)
]
MAGNITUDE_LABELS = [
    "All", "Micro (1.0-1.9)", "Minor (2.0–2.9)", "Minor (3.0-3.9)", "Light (4.0–4.9)",
    "Moderate (5.0–5.9)", "Strong (6.0–6.9)", "Major (7.0–7.9)", "Great (8.0-8.9)"
]
MAGNITUDE_COLORS = ["#FFE500", "#FFC400", "#FFA400", "#FF8300", "#FF6200", "#FF4100", "#FF2100", "#FF0000"]

DEFAULT_MIN_YEAR = 2000
DEFAULT_MAX_YEAR = datetime.now().year