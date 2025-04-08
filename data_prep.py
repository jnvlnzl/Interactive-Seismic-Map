# data_prep.py
import pandas as pd
import geopandas as gpd
from datetime import datetime
import config # Import constants

def load_dataframes():
    """Loads initial dataframes from paths defined in config."""
    try:
        gdf_provinces = gpd.read_file(config.PROVINCES_GEOJSON)
        active_faults = gpd.read_file(config.FAULTS_GEOJSON)
        magnitude_df = pd.read_csv(config.MAGNITUDE_CSV)
        ph_faults = active_faults[active_faults["catalog_name"].str.contains("Philippines", case=False, na=False)]
        print("Dataframes loaded successfully.")
        return gdf_provinces, magnitude_df, ph_faults
    except Exception as e:
        print(f"FATAL ERROR LOADING CORE DATA: {e}. Returning empty structures.")
        return gpd.GeoDataFrame(), pd.DataFrame(), gpd.GeoDataFrame()

def prepare_map_data(gdf_provinces, magnitude_df):
    """Prepares province averages and population data for the main map."""
    province_ave_magnitudes = pd.DataFrame()
    population_df = pd.DataFrame(columns=["Province", "2020", "2015", "2010", "2000"]) # Define columns even if empty

    if magnitude_df.empty or gdf_provinces.empty:
        print("Warning: Cannot prepare map data due to missing input dataframes.")
        return province_ave_magnitudes, population_df

    try:
        # --- Population processing ---
        pop_df = magnitude_df.copy() # Work on a copy
        for col in ['2020', '2015', '2010', '2000']:
            if col in pop_df.columns:
                # Use errors='coerce' to handle non-numeric values gracefully
                pop_df[col] = pd.to_numeric(pop_df[col].astype(str).str.replace(',', '', regex=False), errors='coerce')
            else:
                 pop_df[col] = 0 # Add column if missing

        if "Province" in pop_df.columns:
            # Drop rows where Province is NaN before dropping duplicates
            population_df = pop_df.dropna(subset=['Province'])[["Province", "2020", "2015", "2010", "2000"]].drop_duplicates("Province")
            # Fill NaNs resulting from coerce or missing data with 0 AFTER dropping duplicates
            for col in ['2020', '2015', '2010', '2000']:
                population_df[col] = population_df[col].fillna(0).astype(int)
        else:
             print("Warning: 'Province' column missing for population data prep.")


        # --- Average magnitude processing ---
        if 'Longitude' in magnitude_df.columns and 'Latitude' in magnitude_df.columns:
            magnitude_gdf = gpd.GeoDataFrame(
                magnitude_df, geometry=gpd.points_from_xy(magnitude_df["Longitude"], magnitude_df["Latitude"]), crs="EPSG:4326"
            )
            if not magnitude_gdf.empty:
                try:
                    # Ensure target GeoDataFrame has necessary columns
                    target_gdf = gdf_provinces[['adm2_en', 'geometry']].copy()
                    # Use inner join
                    magnitude_gdf_joined = gpd.sjoin(magnitude_gdf, target_gdf, how="inner", predicate="intersects")
                    # Calculate average magnitude only if join was successful and resulted in data
                    if not magnitude_gdf_joined.empty and 'adm2_en' in magnitude_gdf_joined.columns and 'Magnitude' in magnitude_gdf_joined.columns:
                         province_ave_magnitudes = magnitude_gdf_joined.groupby("adm2_en")["Magnitude"].mean().reset_index()
                    else:
                         print("Warning: Spatial join resulted in empty dataframe or missing columns.")
                except Exception as sjoin_err:
                     print(f"Warning: Spatial join failed: {sjoin_err}")
        else:
            print("Warning: Longitude/Latitude columns missing for spatial join.")

        print("Map data prepared.")
        return province_ave_magnitudes, population_df

    except Exception as e:
        print(f"ERROR preparing map data: {e}")
        # Return empty but correctly structured dataframes on error
        return pd.DataFrame(), pd.DataFrame(columns=["Province", "2020", "2015", "2010", "2000"])


def prepare_line_chart_data(magnitude_df):
    """Prepares data using the exact logic from the user script."""
    # Initialize default/empty values
    earthquake_counts = pd.DataFrame()
    overall_counts = pd.DataFrame()
    provinces, regions, island_groups = [], [], []
    min_year, max_year = config.DEFAULT_MIN_YEAR, config.DEFAULT_MAX_YEAR
    available_years = list(range(min_year, max_year + 1))

    if magnitude_df.empty:
        print("Warning: Cannot prepare line chart data, magnitude_df is empty.")
        return earthquake_counts, overall_counts, provinces, regions, island_groups, min_year, max_year, available_years

    try:
        df = magnitude_df.copy() # Work on a copy
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # Drop rows where date conversion failed or date is NaT
        df.dropna(subset=['Date'], inplace=True)
        df['Year'] = df['Date'].dt.year

        grouping_cols = ['Year', 'Province', 'Region', 'Island Group']
        if all(col in df.columns for col in grouping_cols):
            # Drop rows with NaN in essential grouping columns before grouping
            clean_df = df.dropna(subset=grouping_cols)
            if not clean_df.empty:
                earthquake_counts = clean_df.groupby(grouping_cols).size().reset_index(name='Number of Earthquakes')
                overall_counts = clean_df.groupby('Year').size().reset_index(name='Number of Earthquakes')

                # Get unique lists from the aggregated data
                provinces = sorted(earthquake_counts['Province'].unique())
                regions = sorted(earthquake_counts['Region'].unique())
                island_groups = sorted(earthquake_counts['Island Group'].unique())

                if not earthquake_counts.empty:
                    min_year = int(earthquake_counts['Year'].min())
                    max_year = int(earthquake_counts['Year'].max())
                    available_years = sorted(earthquake_counts['Year'].unique())
                else:
                     print("Warning: earthquake_counts is empty after grouping.")
            else:
                print("Warning: Dataframe became empty after cleaning NaNs in grouping columns.")
        else:
            missing_cols = [col for col in grouping_cols if col not in df.columns]
            print(f"Warning: Missing required columns for line chart aggregation: {missing_cols}")

        print("Line chart data prepared.")
        return earthquake_counts, overall_counts, provinces, regions, island_groups, min_year, max_year, available_years

    except Exception as e:
        print(f"ERROR preparing line chart data: {e}")
        # Return defaults on error
        return pd.DataFrame(), pd.DataFrame(), [], [], [], config.DEFAULT_MIN_YEAR, config.DEFAULT_MAX_YEAR, list(range(config.DEFAULT_MIN_YEAR, config.DEFAULT_MAX_YEAR + 1))