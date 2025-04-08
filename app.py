# app.py (Main Entry Point)
import dash
from dash import Dash, html 
import data_prep 
from layout import create_layout 
import config 

app = Dash(__name__,
           external_stylesheets=[config.CSS_FILE_RELATIVE], 
           suppress_callback_exceptions=True)
app.title = "PH Earthquake Explorer"

print("Loading data...")
gdf_provinces, magnitude_df_raw, ph_faults = data_prep.load_dataframes()
print("Preparing map data...")
province_ave_magnitudes, population_df = data_prep.prepare_map_data(gdf_provinces, magnitude_df_raw.copy())
print("Preparing line chart data...")
earthquake_counts, overall_counts, provinces, regions, island_groups, min_year, max_year, available_years = data_prep.prepare_line_chart_data(magnitude_df_raw.copy())
print("Data preparation complete.")

app.layout = create_layout(min_year, max_year, available_years)

import callbacks

server = app.server

# --- Run Locally ---
if __name__ == "__main__":
    print(f"Starting Dash server on http://127.0.0.1:8050")
    # Set debug=False for production or checking deployment readiness
    # Set debug=True for development (enables hot-reloading, error pages)
    app.run(debug=False, host='0.0.0.0', port=8050)