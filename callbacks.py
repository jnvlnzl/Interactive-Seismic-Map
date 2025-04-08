# callbacks.py
from dash import Input, Output, State, callback, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import traceback

# Import the app object and prepared data from the main app file
from app import (
    app, gdf_provinces, ph_faults, province_ave_magnitudes, population_df,
    magnitude_df_raw, # Raw DF as loaded in app.py
    earthquake_counts, overall_counts, provinces, regions, island_groups,
    available_years, min_year, max_year
)
import config # Import constants if needed

print("Registering callbacks...")

# --- Callback Definitions ---

# Callback to update the main Choropleth Map
@callback(
    Output("earthquake-map", "figure"),
    Input("magnitude-slider", "value"),
    Input("fault-toggle", "value")
)
def update_map(idx, fault_toggle):
    # Uses province_ave_magnitudes, population_df, ph_faults, gdf_provinces imported from app.py
    fig = go.Figure() # Initialize empty figure
    try:
        choro_data = pd.DataFrame()
        color_scale = config.MAGNITUDE_COLORS[0] # Default color - this logic needs refinement based on usage
        range_color = [1, 5] # Default range
        show_scale_bar = False

        if not (0 <= idx < len(config.MAGNITUDE_RANGES)):
            raise ValueError("Invalid magnitude slider index")

        # Prepare data for choropleth based on slider
        if config.MAGNITUDE_RANGES[idx] is None: # "All" selected
            if province_ave_magnitudes.empty: raise ValueError("Missing average magnitude data")
            choro_data = province_ave_magnitudes.copy()
            color_scale = px.colors.sequential.YlOrRd # Use a scale for "All"
            if 'Magnitude' in choro_data.columns and not choro_data['Magnitude'].isnull().all():
                 range_color = [choro_data['Magnitude'].min(), choro_data['Magnitude'].max()]
            show_scale_bar = True
        else: # Specific magnitude range selected
            if province_ave_magnitudes.empty: raise ValueError("Missing average magnitude data")
            min_mag, max_mag = config.MAGNITUDE_RANGES[idx]
            choro_data = province_ave_magnitudes[
                (province_ave_magnitudes["Magnitude"] >= min_mag) &
                (province_ave_magnitudes["Magnitude"] <= max_mag) ].copy()
            if idx - 1 >= 0 and idx - 1 < len(config.MAGNITUDE_COLORS):
                 single_color = config.MAGNITUDE_COLORS[idx - 1]
            else: single_color = "#CCCCCC" # Default grey
            color_scale = [[0, single_color], [1, single_color]] # Fixed color scale
            range_color = [min_mag, max_mag]
            show_scale_bar = False

        if choro_data.empty and config.MAGNITUDE_RANGES[idx] is not None:
             fig.update_layout(title=f"No provinces with avg magnitude {config.MAGNITUDE_LABELS[idx]}")
             return fig

        # Merge population data for hover info
        custom_data_array = np.array([[]])
        pop_cols = ["2020", "2015", "2010", "2000"]
        hover_template_pop = "Population data unavailable<extra></extra>"
        if not population_df.empty and 'Province' in population_df.columns and 'adm2_en' in choro_data.columns:
            # Ensure merge keys are clean (e.g., strip whitespace) if necessary before merge
            # choro_data['adm2_en'] = choro_data['adm2_en'].str.strip()
            # population_df['Province'] = population_df['Province'].str.strip()
            choro_data = choro_data.merge(population_df, left_on="adm2_en", right_on="Province", how="left")
            for col in pop_cols: choro_data[col] = choro_data[col].fillna(0) # Fill NaNs introduced by merge
            custom_data_array = choro_data[pop_cols].values
            hover_template_pop = ("Pop (2020): %{customdata[0]:,}<br>" + "Pop (2015): %{customdata[1]:,}<br>" +
                                  "Pop (2010): %{customdata[2]:,}<br>" + "Pop (2000): %{customdata[3]:,}<extra></extra>")

        # Add Choropleth trace
        if not choro_data.empty and not gdf_provinces.empty:
            fig.add_trace(go.Choroplethmapbox(
                geojson=gdf_provinces.__geo_interface__, locations=choro_data["adm2_en"], z=choro_data["Magnitude"],
                featureidkey="properties.adm2_en", colorscale=color_scale, zmin=range_color[0], zmax=range_color[1],
                marker_opacity=0.7, marker_line_width=0.5, showscale=show_scale_bar,
                colorbar_title="Avg Magnitude" if show_scale_bar else "",
                customdata=custom_data_array if custom_data_array.size > 0 else None,
                hovertemplate=("<b>%{location}</b><br>" + "Average Magnitude: %{z:.2f}<br>" + hover_template_pop)
            ))
        elif gdf_provinces.empty:
             print("Warning: gdf_ph_provinces is empty, cannot draw map.")


        # Overlay fault lines
        if fault_toggle and not ph_faults.empty:
            for _, row in ph_faults.iterrows():
                geom = row.geometry
                if geom and not geom.is_empty:
                    lines_to_plot = list(geom.geoms) if geom.geom_type == 'MultiLineString' else [geom]
                    for line in lines_to_plot:
                        if line and not line.is_empty:
                             lon, lat = line.xy
                             fig.add_trace(go.Scattermapbox(mode="lines", lon=list(lon), lat=list(lat),
                                                             line=dict(width=1, color='black'), showlegend=False, hoverinfo='none'))

        # Update Layout
        fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=config.DEFAULT_ZOOM,
                          mapbox_center=config.DEFAULT_CENTER, margin={"r":0,"t":0,"l":0,"b":0}, clickmode='event+select')
        return fig

    except Exception as e:
        traceback.print_exc()
        return go.Figure(layout={"title": "Error updating map"})


# Callback to handle map clicks -> Show Detail View
@callback(
    Output("main-map-container", "style", allow_duplicate=True),
    Output("main-controls", "style", allow_duplicate=True),
    Output("detail-view-container", "style", allow_duplicate=True),
    Output("back-button", "style", allow_duplicate=True),
    Output("click-data", "children", allow_duplicate=True),
    Output("province-title", "children", allow_duplicate=True),
    Output("line-chart-filter-type", "value", allow_duplicate=True),
    Output("line-chart-filter-selector", "value", allow_duplicate=True),
    Input("earthquake-map", "clickData"),
    prevent_initial_call=True
)
def handle_map_click(clickData):
    if clickData is None or not clickData.get('points'): return [no_update] * 8
    try:
         clicked_province_map_key = clickData['points'][0].get('location')
         if clicked_province_map_key is None: return [no_update] * 8
         # --- Adjust key mapping if needed ---
         # Assumes the map key ('adm2_en') can be directly used to select in the line chart's 'Province' list.
         # If not, you need a mapping: e.g., find 'Province' where 'adm2_en' matches in gdf_provinces.
         clicked_province_select_key = clicked_province_map_key

         # Check if the key exists in the line chart province list for safety
         if clicked_province_select_key not in provinces:
             print(f"Warning: Clicked map key '{clicked_province_select_key}' not found in line chart province list. Cannot pre-select.")
             line_chart_filter_selector_init = [] # Don't pre-select if key doesn't match
         else:
             line_chart_filter_selector_init = [clicked_province_select_key]

         main_map_style, main_controls_style = {"display": "none"}, {"display": "none"}
         detail_view_style, back_button_style = {"display": "flex"}, {"display": "block"}
         province_title_bubble = f"Details for: {clicked_province_map_key}"
         click_data_store = clicked_province_map_key
         line_chart_filter_type_init = "Province" # Default to Province filter

         return (main_map_style, main_controls_style, detail_view_style, back_button_style,
                 click_data_store, province_title_bubble,
                 line_chart_filter_type_init, line_chart_filter_selector_init)
    except Exception as e:
         traceback.print_exc(); return [no_update] * 8


# Callback for Back Button -> Show Main Map
@callback(
    Output("main-map-container", "style", allow_duplicate=True),
    Output("main-controls", "style", allow_duplicate=True),
    Output("detail-view-container", "style", allow_duplicate=True),
    Output("back-button", "style", allow_duplicate=True),
    Output("click-data", "children", allow_duplicate=True),
    Output("line-chart-overall-toggle", "value", allow_duplicate=True),
    Output("line-chart-filter-type", "value", allow_duplicate=True),
    Output("line-chart-filter-selector", "value", allow_duplicate=True),
    Output("line-chart-year-slider", "value", allow_duplicate=True),
    Input("back-button", "n_clicks"),
    prevent_initial_call=True
)
def go_back_to_main_map(n_clicks):
    if n_clicks is None: return [no_update] * 9
    try:
        line_chart_overall_reset, line_chart_filter_type_reset = ["overall"], None
        line_chart_filter_selector_reset, line_chart_year_slider_reset = [], [min_year, max_year]
        main_map_style, main_controls_style = {"display": "block"}, {"display": "block"}
        detail_view_style, back_button_style = {"display": "none"}, {"display": "none"}
        click_data_store = None
        return (main_map_style, main_controls_style, detail_view_style, back_button_style,
                click_data_store, line_chart_overall_reset, line_chart_filter_type_reset,
                line_chart_filter_selector_reset, line_chart_year_slider_reset)
    except Exception as e:
        traceback.print_exc(); return [no_update] * 9


# Callback to update Bubble Map
@callback(
    Output("bubble-map", "figure"),
    Input("click-data", "children"), # This holds clicked_province_map_key (likely 'adm2_en')
    Input("bubble-year-slider", "value")
)
def update_bubble_map(clicked_province_map_key, year_range):
    # Uses magnitude_df_raw, gdf_provinces imported from app.py
    if not clicked_province_map_key:
        return go.Figure(layout={"title": "Click province on map first", "template": "plotly_white"})
    try:
        start_yr, end_yr = year_range
        # --- IMPORTANT: Filter raw data based on map key ---
        # If map key ('adm2_en') is different from 'Province' column used in raw data,
        # you need a way to link them. Assuming 'Province' column is reliable in magnitude_df_raw
        # AND that clicked_province_map_key can be used directly (requires consistent naming or mapping).
        # Adjust this filter if needed.
        filtered_eq = magnitude_df_raw[
            (magnitude_df_raw['Province'] == clicked_province_map_key) # Adjust if key doesn't match 'Province'
          & (magnitude_df_raw['Year'] >= start_yr)
          & (magnitude_df_raw['Year'] <= end_yr)
        ].copy() if not magnitude_df_raw.empty else pd.DataFrame()

        if filtered_eq.empty:
             return go.Figure(layout={"title": f"No Bubble Data ({start_yr}-{end_yr}) for {clicked_province_map_key}", "template": "plotly_white"})

        fig_bubble = px.scatter_mapbox(
             filtered_eq, lat="Latitude", lon="Longitude", size="Magnitude", color="Magnitude",
             color_continuous_scale=px.colors.sequential.Reds, size_max=15,
             hover_name="Location",
             hover_data={ # Customize hover info
                "Magnitude": ":.1f", "Depth_In_Km": ":.1f km", "Date": "|%Y-%m-%d",
                "Province": True, "Latitude": False, "Longitude": False
            }
        )
        # Add centering logic
        center_lat, center_lon, zoom = config.DEFAULT_CENTER['lat'], config.DEFAULT_CENTER['lon'], 6
        if not gdf_provinces.empty:
             # Assumes clicked_province_map_key matches 'adm2_en' in gdf_provinces
             prov_geom_series = gdf_provinces[gdf_provinces['adm2_en'] == clicked_province_map_key].geometry
             if not prov_geom_series.empty:
                  prov_geom = prov_geom_series.iloc[0]
                  if prov_geom and not prov_geom.is_empty:
                      bounds = prov_geom.bounds
                      center_lon, center_lat = (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2; zoom = 7
        fig_bubble.update_layout(mapbox_style="carto-positron", mapbox_center={"lat": center_lat, "lon": center_lon}, mapbox_zoom=zoom, margin={"r":0,"t":0,"l":0,"b":0})
        return fig_bubble
    except Exception as e:
        traceback.print_exc(); return go.Figure(layout={"title": "Error loading bubble map"})


# --- Callbacks for Line Chart Explorer ---
@callback(
    Output("line-chart-filter-selector-container", "style"),
    Output("line-chart-filter-selector", "options"),
    Input("line-chart-filter-type", "value")
)
def update_line_chart_checklist(filter_type):
    # Uses provinces, regions, island_groups lists imported from app.py
    options, style = [], {"display": "none"}
    if filter_type == "Province": options = [{"label": p, "value": p} for p in provinces]
    elif filter_type == "Region": options = [{"label": r, "value": r} for r in regions]
    elif filter_type == "Island Group": options = [{"label": i, "value": i} for i in island_groups]
    if options: style = {"display": "block"}
    return style, options

@callback(
    Output("line-chart-graph", "figure"),
    Input("line-chart-filter-selector", "value"),
    Input("line-chart-filter-type", "value"),
    Input("line-chart-overall-toggle", "value"),
    Input("line-chart-year-slider", "value")
)
def update_line_chart_explorer_graph(selected_values, filter_type, overall_toggle, year_range):
    # Uses earthquake_counts, overall_counts etc. imported from app.py
    if earthquake_counts.empty or overall_counts.empty: return go.Figure(layout={"title": "Data unavailable"})
    try:
        start_year, end_year = year_range
        filtered_ec = earthquake_counts[(earthquake_counts['Year'] >= start_year) & (earthquake_counts['Year'] <= end_year)]
        filtered_oc = overall_counts[(overall_counts['Year'] >= start_year) & (overall_counts['Year'] <= end_year)]
        fig = go.Figure()
        fig.update_layout(title="Earthquake Trends Explorer", xaxis_title="Year", yaxis_title="Number of Earthquakes", template="plotly_white", margin=dict(l=40, r=20, t=60, b=40),
                          xaxis=dict(tickmode='array', tickvals=available_years, ticktext=[str(y) for y in available_years], range=[start_year - 0.5, end_year + 0.5]))
        traces_added = False
        # Add traces based on toggles and selections...
        # (Keep the trace adding logic from the previous clean version)
        if "overall" in overall_toggle and not filtered_oc.empty: fig.add_trace(go.Scatter(x=filtered_oc["Year"], y=filtered_oc["Number of Earthquakes"], mode="lines", name="Overall", line=dict(dash="dot"))); traces_added=True
        if "overall_provinces" in overall_toggle:
            agg = filtered_ec.groupby(['Year', 'Province'])['Number of Earthquakes'].sum().reset_index();
            for p in provinces: d = agg[agg['Province'] == p]; fig.add_trace(go.Scatter(x=d["Year"], y=d["Number of Earthquakes"], mode="lines", name=p)); traces_added=True
        if "overall_regions" in overall_toggle:
            agg = filtered_ec.groupby(['Year', 'Region'])['Number of Earthquakes'].sum().reset_index();
            for r in regions: d = agg[agg['Region'] == r]; fig.add_trace(go.Scatter(x=d["Year"], y=d["Number of Earthquakes"], mode="lines", name=r)); traces_added=True
        if "overall_island_groups" in overall_toggle:
            agg = filtered_ec.groupby(['Year', 'Island Group'])['Number of Earthquakes'].sum().reset_index();
            for i in island_groups: d = agg[agg['Island Group'] == i]; fig.add_trace(go.Scatter(x=d["Year"], y=d["Number of Earthquakes"], mode="lines", name=i)); traces_added=True
        if selected_values and filter_type:
            f_data = filtered_ec[filtered_ec[filter_type].isin(selected_values)]
            if not f_data.empty:
                agg_cols = ['Year', filter_type]; agg = f_data.groupby(agg_cols)['Number of Earthquakes'].sum().reset_index()
                for item in selected_values:
                    subset = agg[agg[filter_type] == item]
                    if not subset.empty: fig.add_trace(go.Scatter(x=subset["Year"], y=subset["Number of Earthquakes"], mode="lines+markers", name=item)); traces_added=True
        if not traces_added: fig.update_layout(title="Select options or adjust year range")
        return fig
    except Exception as e:
        traceback.print_exc(); return go.Figure(layout={"title": "Error generating line chart"})

print("Callbacks registered.")