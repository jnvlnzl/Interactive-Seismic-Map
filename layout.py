# layout.py
from dash import dcc, html
import dash_daq as daq
import config # Import constants/labels

# Function to create the layout structure
def create_layout(min_year_data, max_year_data, available_years_data):
    """Creates the Dash app layout."""
    layout = html.Div([
        html.Div(id='main-controls', style={'display': 'block'}, children=[
            html.Label("Select Average Earthquake Magnitude Range"),
            html.Div(
                dcc.Slider(id="magnitude-slider",
                           min=0, max=len(config.MAGNITUDE_RANGES) - 1, value=0, step=1,
                           marks={i: {"label": label.replace(" ", "\\n"), "style": {"white-space": "pre-line"}} for i, label in enumerate(config.MAGNITUDE_LABELS)},
                           className="colored-slider"),
                style={"margin-bottom": "15px"}
            ),
            html.Div([html.Label("Show Fault Lines", style={"margin-right": "10px"}), daq.ToggleSwitch(id="fault-toggle", value=True, color="#333")],
                     style={"display": "flex", "alignItems": "center", "margin-bottom": "20px"}),
        ]),

        # --- Main Map Container ---
        html.Div(id='main-map-container', style={'display': 'block', 'height': '75vh'}, children=[
            dcc.Loading(id="loading-main-map", children=dcc.Graph(id="earthquake-map", style={'height': '100%'}))
        ]),

        # --- Detail View Area (Hidden Initially) ---
        html.Div(id='detail-view-container', style={'display': 'none', 'flexDirection': 'row', 'height': '85vh'}, children=[
            # Bubble Map Wrapper
            html.Div(id='bubble-map-wrapper', style={'flex': '2', 'paddingRight': '10px', 'display': 'flex', 'flexDirection': 'column'}, children=[
                 html.H3(id="province-title", style={'textAlign': 'center', 'flexShrink': 0}),
                 html.Label("Filter Bubble Map by Year:", style={'flexShrink': 0, 'marginLeft': '15px'}),
                 html.Div(
                     dcc.RangeSlider(id="bubble-year-slider", # Unique ID
                                     min=min_year_data, max=max_year_data, value=[min_year_data, max_year_data], step=1,
                                     marks={str(year): str(year) for year in available_years_data}, ),
                     style={'margin': '0 15px 15px 15px', 'flexShrink': 0}
                 ),
                 dcc.Loading(id="loading-bubble-map", children=dcc.Graph(id="bubble-map", style={'flexGrow': 1, 'minHeight': 0}))
            ]),
            # Line Chart Explorer Wrapper
            html.Div(id='line-chart-explorer-wrapper', style={'flex': '3', 'display': 'flex', 'borderLeft': '1px solid #ccc'}, children=[
                # Sidebar
                html.Div([
                    html.H4("Options:", style={'marginTop':'0px'}),
                    dcc.Checklist(id="line-chart-overall-toggle", options=[{"label": "Overall Earthquakes", "value": "overall"}, {"label": "Overall Provinces", "value": "overall_provinces"}, {"label": "Overall Regions", "value": "overall_regions"}, {"label": "Overall Island Groups", "value": "overall_island_groups"}], value=["overall"]),
                    html.Br(), html.Label("Sort by:"), html.Br(), html.Br(),
                    dcc.Dropdown(id="line-chart-filter-type", options=[{"label": "Province", "value": "Province"}, {"label": "Region", "value": "Region"}, {"label": "Island Group", "value": "Island Group"}], placeholder="Select Filter Type"),
                    html.Div(id="line-chart-filter-selector-container", children=[dcc.Checklist(id="line-chart-filter-selector", value=[])], style={"display": "none", "maxHeight": "250px", "overflowY": "scroll"}),
                ], style={"width": "250px", "overflowY": "auto", "borderRight": "1px solid #ccc", "padding": "10px", "flexShrink": 0, "backgroundColor": "#f9f9f9"}),
                # Main Graph Area
                html.Div([
                    html.Label("Select Year Range:", style={'marginLeft': '15px'}),
                     html.Div(
                        dcc.RangeSlider(id="line-chart-year-slider", # Unique ID
                                        min=min_year_data, max=max_year_data, step=None, value=[min_year_data, max_year_data],
                                        marks={str(year): str(year) for year in available_years_data},),
                        style={'margin': '0 15px 15px 15px'}
                     ),
                    html.Br(),
                    dcc.Loading(id='loading-line-chart-explorer', children=dcc.Graph(id="line-chart-graph"))
                ], style={"flexGrow": 1, 'display': 'flex', 'flexDirection': 'column'})
            ]),
        ]),
        # --- Controls outside ---
        html.Button("Back to Main Map", id="back-button", className="back-button-styled", style={"display": "none", 'marginTop': '15px'}),
        html.Div(id="click-data", style={"display": "none"}), # Hidden storage for clicked province
    ])
    return layout