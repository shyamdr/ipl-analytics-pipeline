import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def initialize_session_state():
    """Initializes session state variables if they don't exist."""
    defaults = {
        'chart_type': 'Bar Chart',
        'active_filters': {},
        'filter_to_remove': None,

        # --- Bar Chart Keys ---
        'config_category_col': None,
        'config_value_cols': [],
        'config_color_col': None,
        'config_orientation': 'Horizontal',
        'config_barmode': 'group',
        'bar_chart_summarize_toggle': False,
        'bar_chart_group_by_cols': [],
        # --- Line Chart Keys ---
        'config_x_col_line': None,
        'config_y_cols_line': [],
        'config_color_col_line': None,
        'config_markers_line': True,
        'config_area_fill_line': False,
        'config_trendline_line': False,
        'line_chart_summarize_toggle': False,
        'line_chart_group_by_cols': [],
        # --- Donut Chart ---
        'config_names_col_donut': None,
        'config_values_col_donut': None,
        # --- Sunburst Chart ---
        'config_path_sunburst': [],
        'config_values_sunburst': None,
        # --- Nightingale Chart ---
        'config_theta_nightingale': None,
        'config_r_nightingale': None,
        'nightingale_rose_chart_summarize_toggle': False,
        'nightingale_rose_chart_group_by_cols': [],
        # --- Scatter Plot ---
        'config_x_col_scatter': None,
        'config_y_col_scatter': None,
        'config_color_col_scatter': None,
        'config_size_col_scatter': None,  # For the Bubble Chart variant
        'config_trendline_scatter': 'None',  # Use a string for trendline options
        'scatter_plot_summarize_toggle': False,
        'scatter_plot_group_by_cols': [],
        # --- Histogram ---
        'config_x_col_hist': None,
        'config_color_col_hist': None,
        'config_nbins_hist': 30,  # Default to 30 bins
        'config_barmode_hist': 'overlay',  # Default to overlay
        'config_hist_type': 'Histogram',
        # --- Box Plot ---
        'config_x_col_box': None,  # For the categorical axis
        'config_y_col_box': None,  # For the numeric axis
        'config_color_col_box': None,  # To split by color
        'config_plot_type_box': 'Box',  # To switch between Box and Violin
        'config_points_box': False,  # To show/hide all data points
        'box_plot_summarize_toggle': False,
        'box_plot_group_by_cols': [],
        # --- Heat Map ---
        'config_x_col_heat': None,  # The column for the X-axis categories
        'config_y_col_heat': None,  # The column for the Y-axis categories
        'config_z_col_heat': None,  # The numeric column for the color value
        'config_text_auto_heat': True,  # To show/hide the text values on cells
        'config_color_scale_heat': 'Reds',  # Default color theme
        'heatmap_summarize_toggle': False,  # Note: Summarization is less common for heatmaps
        'heatmap_group_by_cols': [],
        # --- Radar Chart ---
        'config_items_radar': [],  # The items to compare (e.g., player names)
        'config_metrics_radar': [],  # The numeric metrics for the axes
        'config_item_col_radar': None,  # The column containing the items to compare
        # --- TreeMap ---
        'config_path_treemap': [],  # For the hierarchy levels
        'config_values_treemap': None,  # For the size of the rectangles
        'config_color_treemap': None,
        # Sankey Chart ---
        'config_source_sankey': None,  # The "from" column
        'config_target_sankey': None,  # The "to" column
        'config_value_sankey': None,
        # A dictionary to hold aggregation function choices for each chart
        'agg_configs': {}  # <-- ADD
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_eligible_charts(df):
    """
    Analyzes the DataFrame's structure to determine which chart types are possible.
    """
    eligible_charts = []

    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    categorical_cols = [col for col in df.columns if df[col].dtype == 'object']

    num_numeric = len(numeric_cols)
    num_categorical = len(categorical_cols)

    # --- Define data requirements for each chart type ---
    CHART_REQUIREMENTS = {
        # Standard Charts
        "Bar Chart": num_numeric >= 1 and num_categorical >= 1,
        "Line Chart": num_numeric >= 1 and df.shape[0] > 1,
        "Scatter Plot": num_numeric >= 2,
        "Pie Chart": num_numeric == 1 and num_categorical == 1,
        "Bubble Chart": num_numeric >= 3,
        # Distribution Charts
        "Histogram": num_numeric >= 1,
        "Box Plot": num_numeric >= 1,
        "Violin Plot": num_numeric >= 1,
        # Hierarchical / Part-of-a-Whole Charts
        "Treemap": num_numeric == 1 and num_categorical >= 1,
        "Sunburst Chart": num_numeric == 1 and num_categorical >= 1,
        # Relational / Flow Charts
        "Heatmap": num_numeric == 1 and num_categorical >= 2,
        "Radar Chart": num_numeric >= 3 and num_categorical >= 1,  # Needs multiple metrics to compare
        "Sankey Diagram": num_numeric == 1 and num_categorical == 2,  # Ideal for source -> target flows
        "Funnel Chart": num_numeric >= 1 and num_categorical >= 1,
    }

    for chart, is_possible in CHART_REQUIREMENTS.items():
        if is_possible:
            eligible_charts.append(chart)

    return sorted(eligible_charts), numeric_cols, categorical_cols

def build_chart_studio(df):
    """
    Renders a single, stateful, and modular Chart Studio UI that adapts to user selections.
    This version corrects the order of operations to fix the summarization bug.
    """
    st.write("---")
    st.write("### Chart Studio")

    # Clean the dataframe once
    df_clean = clean_dataframe(df)
    if df_clean.empty:
        st.info("The query returned no data to visualize.")
        return

    # Initialize all session state variables if they don't exist
    initialize_session_state()

    if st.session_state.filter_to_remove:
        col_to_del = st.session_state.filter_to_remove
        if col_to_del in st.session_state.active_filters:
            del st.session_state.active_filters[col_to_del]
        # Reset the flag so this action doesn't repeat on the next run
        st.session_state.filter_to_remove = None

    # --- TOP-LEVEL CHART TYPE SELECTOR ---
    st.selectbox(
        "Choose a chart type to build:",
        options=["Bar Chart", "Line Chart", "Donut Chart", "Sunburst Chart", "Nightingale Rose Chart", "Scatter Plot",
                 "Histogram", "Box Plot", "Heatmap", "Radar Chart", "Treemap", "Sankey Diagram"],
        key='chart_type'  # Bind this to session state
    )

    # --- RENDER ALL UI TABS FIRST to capture user input into session_state ---
    tab_config, tab_summary, tab_filter = st.tabs([
        "📊 Configure Chart",
        "⚙️ Summarize Data",
        "🔍 Filter Data"
    ])

    with tab_filter:
        render_filter_tab(df_clean)  # Pass the original clean df for filter options

    # The config tab will determine which columns are available for summarization
    with tab_config:
        if st.session_state.chart_type == 'Bar Chart':
            render_bar_chart_config(df_clean)  # Pass df_clean to get full list of columns
        elif st.session_state.chart_type == 'Line Chart':
            render_line_chart_config(df_clean)
        elif st.session_state.chart_type == 'Donut Chart':
            render_donut_chart_config(df_clean)
        elif st.session_state.chart_type == 'Sunburst Chart':
            render_sunburst_chart_config(df_clean)
        elif st.session_state.chart_type == 'Nightingale Rose Chart':
            render_nightingale_chart_config(df_clean)
        elif st.session_state.chart_type == 'Scatter Plot':
            render_scatter_plot_config(df_clean)
        elif st.session_state.chart_type == 'Histogram':
            render_histogram_config(df_clean)
        elif st.session_state.chart_type == 'Box Plot':
            render_box_plot_config(df_clean)
        elif st.session_state.chart_type == 'Heatmap':
            render_heatmap_config(df_clean)
        elif st.session_state.chart_type == 'Radar Chart':
            render_radar_chart_config(df_clean)
        elif st.session_state.chart_type == 'Treemap':
            render_treemap_config(df_clean)
        elif st.session_state.chart_type == 'Sankey Diagram':
            render_sankey_diagram_config(df_clean)

    with tab_summary:
        # Pass df_clean so the Group By dropdown has all categorical columns
        render_summary_tab(df_clean)

    # This ensures we use the most up-to-date selections from session_state
    df_processed = process_data(df_clean)

    # --- RENDER THE PLOT PREVIEW using the correctly processed data ---
    st.write("---")
    st.write("### Chart Preview")

    if st.session_state.chart_type == 'Bar Chart':
        create_bar_chart_from_state(df_processed)
    elif st.session_state.chart_type == 'Line Chart':
        create_line_chart_from_state(df_processed)
    elif st.session_state.chart_type == 'Donut Chart':
        create_donut_chart_from_state(df_processed)
    elif st.session_state.chart_type == 'Sunburst Chart':
        create_sunburst_chart_from_state(df_processed)
    elif st.session_state.chart_type == 'Nightingale Rose Chart':
        create_nightingale_chart_from_state(df_processed)
    elif st.session_state.chart_type == 'Scatter Plot':
        create_scatter_plot_from_state(df_processed)
    elif st.session_state.chart_type == 'Histogram':
        create_histogram_from_state(df_processed)
    elif st.session_state.chart_type == 'Box Plot':
        create_box_plot_from_state(df_processed)
    elif st.session_state.chart_type == 'Heatmap':
        create_heatmap_from_state(df_processed)
    elif st.session_state.chart_type == 'Radar Chart':
        create_radar_chart_from_state(df_processed)
    elif st.session_state.chart_type == 'Treemap':
        create_treemap_from_state(df_processed)
    elif st.session_state.chart_type == 'Sankey Diagram':
        create_sankey_diagram_from_state(df_processed)

def process_data(df):
    """
    Applies filtering and aggregation using chart-specific session state keys.
    This version now preserves axis columns during aggregation.
    """
    df_processed = df.copy()

    # 1. Apply active filters
    for col, val in st.session_state.get('active_filters', {}).items():
        if col in df_processed.columns:
            if df_processed[col].dtype == 'object':
                df_processed = df_processed[df_processed[col].isin(val)]
            else:
                df_processed = df_processed[df_processed[col].between(val[0], val[1])]

    # 2. Apply summarization if toggled
    active_chart = st.session_state.chart_type
    toggle_key = f"{active_chart.lower().replace(' ', '_')}_summarize_toggle"
    groupby_key = f"{active_chart.lower().replace(' ', '_')}_group_by_cols"

    if st.session_state.get(toggle_key) and st.session_state.get(groupby_key):

        group_by_cols = st.session_state[groupby_key]

        value_cols = []
        axis_cols = []
        color_col = None

        if active_chart == 'Bar Chart':
            value_cols = st.session_state.get('config_value_cols', [])
            axis_cols = [st.session_state.get('config_category_col')]
            color_col = st.session_state.get('config_color_col')
        elif active_chart == 'Line Chart':
            value_cols = st.session_state.get('config_y_cols_line', [])
            axis_cols = [st.session_state.get('config_x_col_line')]
            color_col = st.session_state.get('config_color_col_line')
        elif active_chart == 'Nightingale Rose Chart':
            value_cols = [st.session_state.get('config_r_nightingale')]
            axis_cols = [st.session_state.get('config_theta_nightingale')]
        elif active_chart == 'Scatter Plot':
            # For a scatter plot, all axes (x, y, and size) can be numeric values that need aggregation
            value_cols = [
                st.session_state.get('config_x_col_scatter'),
                st.session_state.get('config_y_col_scatter'),
                st.session_state.get('config_size_col_scatter') # Add the size column
            ]
            # The color column is the categorical axis we need to preserve
            axis_cols = [st.session_state.get('config_color_col_scatter')]
        elif active_chart == 'Box Plot':
            # The y-axis is the numeric value to aggregate
            value_cols = [st.session_state.get('config_y_col_box')]
            # The x-axis and color are the categorical axes to preserve
            axis_cols = [
                st.session_state.get('config_x_col_box'),
                st.session_state.get('config_color_col_box')
            ]
        elif active_chart == 'Heatmap':
            # The z-axis is the numeric value to aggregate
            value_cols = [st.session_state.get('config_z_col_heat')]
            # Both x and y axes are categorical and must be preserved
            axis_cols = [
                st.session_state.get('config_x_col_heat'),
                st.session_state.get('config_y_col_heat')
            ]

        # Filter out None values
        axis_cols = [col for col in axis_cols if col]
        value_cols = [col for col in value_cols if col]

        if not value_cols:
            st.warning("Please select a numeric 'Value' column in the 'Configure Chart' tab before summarizing.")
            return df_processed

        if color_col:
            axis_cols.append(color_col)

        try:
            # Build the aggregation dictionary
            agg_functions = {}
            for col in value_cols:
                agg_func = st.session_state.get(f"agg_{active_chart}_{col}", 'sum').lower()
                agg_functions[col] = agg_func

            for col in axis_cols:
                if col not in group_by_cols and col not in agg_functions:
                    agg_functions[col] = 'first'

            cols_to_process = group_by_cols + list(agg_functions.keys())
            cols_to_process = [c for c in list(dict.fromkeys(cols_to_process)) if c in df_processed.columns]

            df_processed = df_processed[cols_to_process].groupby(group_by_cols).agg(agg_functions).reset_index()
            st.info(f"Data has been summarized by '{', '.join(group_by_cols)}'.")

        except Exception as e:
            st.error(f"Failed to group data. Error: {e}")

    return df_processed

def render_filter_tab(df):
    """Renders the UI for the Filter Data tab."""
    with st.container(border=True):
        st.write("**Add a new filter:**")
        col_to_filter = st.selectbox("Column to filter:", options=df.columns, index=None, placeholder="Choose a column",
                                     key="col_filter_select")

        if col_to_filter:
            if df[col_to_filter].dtype == 'object':
                unique_vals = df[col_to_filter].unique()
                selected_vals = st.multiselect(f"Values for '{col_to_filter}':", options=unique_vals,
                                               key=f"filter_val_{col_to_filter}")
                if st.button("Apply Filter", key=f"apply_{col_to_filter}"):
                    st.session_state.active_filters[col_to_filter] = selected_vals
            elif pd.api.types.is_numeric_dtype(df[col_to_filter]):
                min_val, max_val = float(df[col_to_filter].min()), float(df[col_to_filter].max())
                # Get current filter value if it exists, otherwise use full range
                current_val = st.session_state.active_filters.get(col_to_filter, (min_val, max_val))
                selected_range = st.slider(
                    f"Range for '{col_to_filter}':",
                    min_value=min_val,
                    max_value=max_val,
                    value=current_val,
                    key=f"filter_val_{col_to_filter}"
                )
                if st.button("Apply Filter", key=f"apply_{col_to_filter}"):
                    st.session_state.active_filters[col_to_filter] = selected_range

        if st.session_state.get('active_filters'):
            st.write("**Active Filters:**")
            st.write("double-click to remove existing filters")
            # Create a copy of items to avoid issues while iterating and deleting
            for col, val in list(st.session_state.active_filters.items()):
                if st.button(f"{col}: {str(val)[:30]}... ❌", key=f"del_{col}"):
                    st.session_state.filter_to_remove = col

def render_summary_tab(df):
    """Renders a summary UI that is specific to the selected chart type."""
    with st.container(border=True):
        active_chart = st.session_state.chart_type

        if active_chart in ['Histogram', 'Donut Chart', 'Sunburst Chart', 'Radar Chart', 'Treemap', 'Sankey Diagram']:
            st.info(f"Summarization (Group By) is not applicable for a {active_chart}.")
            return

        # Define keys based on the active chart
        toggle_key = f"{active_chart.lower().replace(' ', '_')}_summarize_toggle"
        groupby_key = f"{active_chart.lower().replace(' ', '_')}_group_by_cols"

        # Check if the chart type supports summarization
        if toggle_key not in st.session_state:
            st.info("Summarization is not applicable for this chart type.")
            return

        col1, col2 = st.columns([1, 2])
        with col1:
            st.toggle("Enable Summarization", key=toggle_key)

        if st.session_state[toggle_key]:
            # Determine which value columns are currently selected in the config tab
            value_cols = []
            if active_chart == 'Bar Chart':
                value_cols = st.session_state.config_value_cols
            elif active_chart == 'Line Chart':
                value_cols = st.session_state.config_y_cols_line
            elif active_chart == 'Nightingale Rose Chart':
                if st.session_state.config_r_nightingale:
                    value_cols = [st.session_state.config_r_nightingale]
            elif active_chart == 'Scatter Plot':
                # For a scatter plot, all axes (x, y, and size) can be aggregated
                potential_cols = [
                    st.session_state.get('config_x_col_scatter'),
                    st.session_state.get('config_y_col_scatter'),
                    st.session_state.get('config_size_col_scatter')
                ]
                # Filter out any that are not selected (i.e., are None)
                value_cols = [col for col in potential_cols if col]
            elif active_chart == 'Box Plot':
                value_cols = [st.session_state.get('config_y_col_box')]
            elif active_chart == 'Heatmap':
                z_col = st.session_state.get('config_z_col_heat')
                if z_col:
                    value_cols = [z_col]

            with col2:
                st.multiselect("Group By:", options=df.select_dtypes(include=['object', 'int64']).columns, key=groupby_key)

            if st.session_state[groupby_key] and value_cols:
                unique_value_cols = list(dict.fromkeys(value_cols))
                st.write("**Define Aggregation for Selected Value Columns:**")
                agg_cols_ui = st.columns(len(unique_value_cols))
                for i, col in enumerate(unique_value_cols):
                    with agg_cols_ui[i]:
                        # Use a unique key for each agg selectbox
                        st.selectbox(f"Agg for '{col}':", options=['sum', 'mean', 'max', 'min', 'count'],
                                     key=f"agg_{active_chart}_{col}")

def render_bar_chart_config(df):
    """Renders the UI for configuring a Bar Chart."""
    with st.container(border=True):
        st.write("**1. Select Axes**")
        plot_numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        plot_categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Category Axis (Text):", options=plot_categorical_cols, key='config_category_col')
        with col2:
            st.multiselect("Value Axis (Numeric):", options=plot_numeric_cols, key='config_value_cols')

        st.write("**2. Select Style**")
        col3, col4, col5 = st.columns(3)
        with col3:
            # Modified version - Select Styles column changes based on the group by field
            summarize_is_on = st.session_state.get('bar_chart_summarize_toggle', False)
            group_by_cols = st.session_state.get('bar_chart_group_by_cols', [])

            # If summarization is ON, the only valid color options are the columns you are grouping by.
            if summarize_is_on and group_by_cols:
                valid_color_options = group_by_cols
            else:
                # Otherwise, all categorical columns are valid options.
                valid_color_options = plot_categorical_cols

            st.selectbox("Color by:", options=[None] + valid_color_options, key='config_color_col',
                         help="When 'Summarize Data' is on, you can only color by a column that you are grouping by.")

        with col4:
            st.radio("Orientation:", ["Horizontal", "Vertical"], horizontal=True, key='config_orientation')
        with col5:
            st.radio("Bar Mode:", ['group', 'stack'], horizontal=True, key='config_barmode')

def create_bar_chart_from_state(df):
    """Plots a bar chart using parameters stored in session_state."""
    # Retrieve all params from session state
    category_col = st.session_state.config_category_col
    value_cols = st.session_state.config_value_cols

    if not category_col or not value_cols:
        st.info("Please configure the chart axes in the 'Configure Chart' tab.")
        return

    try:
        df_sorted = df.sort_values(by=value_cols[0], ascending=(st.session_state.config_orientation == "Horizontal"))
        x_axis, y_axis = (category_col, value_cols) if st.session_state.config_orientation == "Vertical" else (
        value_cols, category_col)

        fig = px.bar(df_sorted, x=x_axis, y=y_axis, color=st.session_state.config_color_col,
                     title=f"{', '.join(value_cols)} by {category_col}", template="plotly_dark",
                     barmode=st.session_state.config_barmode,
                     orientation='v' if st.session_state.config_orientation == 'Vertical' else 'h')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to create chart: {e}")

def render_line_chart_config(df):
    """Renders the UI for configuring a Line Chart."""
    with st.container(border=True):
        st.write("**1. Select Axes**")
        plot_numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        # For line charts, the x-axis can be numeric or categorical (like seasons)
        plot_x_axis_cols = df.columns.tolist()

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("X-Axis (Time or Category):", options=plot_x_axis_cols, key='config_x_col_line')
        with col2:
            st.multiselect("Y-Axis (Values):", options=plot_numeric_cols, key='config_y_cols_line')

        st.write("**2. Select Style**")
        col3, col4, col5 = st.columns(3)
        with col3:
            st.selectbox("Color by (Optional):", options=[None] + plot_x_axis_cols, key='config_color_col_line')
        with col4:
            st.toggle("Show Markers", value=True, key='config_markers_line')
        with col5:
            st.toggle("Fill Area (Area Chart)", value=False, key='config_area_fill_line')

        st.toggle("Show Trendline (for Scatter data)", value=False, key='config_trendline_line',
                  help="Adds a regression line. Best used when X and Y are both numeric.")

def create_line_chart_from_state(df):
    """Plots a line chart using parameters stored in session_state."""
    x_col = st.session_state.config_x_col_line
    y_cols = st.session_state.config_y_cols_line

    if not x_col or not y_cols:
        st.info("Please configure the X-Axis and Y-Axis in the 'Configure Chart' tab.")
        return

    try:
        df_sorted = df.sort_values(by=x_col)

        # Check for area fill option
        area_fill = "tozeroy" if st.session_state.config_area_fill_line else None

        fig = px.line(
            df_sorted,
            x=x_col,
            y=y_cols,
            color=st.session_state.config_color_col_line,
            markers=st.session_state.config_markers_line,
            template="plotly_dark",
            title=f"{', '.join(y_cols)} over {x_col}"
        )

        if area_fill:
            fig.update_traces(fill=area_fill)

        if st.session_state.config_trendline_line:
            # Trendlines work best on scatter plots, so we add them this way
            # Note: This works best for a single Y-axis column
            if len(y_cols) == 1:
                trend_fig = px.scatter(df_sorted, x=x_col, y=y_cols[0], trendline="ols")
                fig.add_trace(trend_fig.data[1])  # Add the trendline trace to the line chart
            else:
                st.warning("Trendline can only be shown for a single Y-Axis selection.")

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to create line chart: {e}")

def render_donut_chart_config(df):
    """Renders the UI for configuring a Donut Chart."""
    with st.container(border=True):
        st.write("**Select Data for Donut Chart**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if not numeric_cols or not categorical_cols:
            st.warning("Donut Charts require at least one numeric and one categorical column.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Labels (Slices):", options=categorical_cols, key='config_names_col_donut')
        with col2:
            st.selectbox("Values (Size of Slices):", options=numeric_cols, key='config_values_col_donut')

def create_donut_chart_from_state(df):
    """Plots a donut chart using parameters stored in session_state."""
    names_col = st.session_state.config_names_col_donut
    values_col = st.session_state.config_values_col_donut

    if not names_col or not values_col:
        st.info("Please configure the Labels and Values in the 'Configure Chart' tab.")
        return
    try:
        df_top = df.nlargest(12, values_col)
        fig = px.pie(df_top, names=names_col, values=values_col, hole=0.4,  # Default hole for donut
                     template="plotly_dark", title=f"Distribution of {values_col} by {names_col}")
        fig.update_traces(textposition='inside', textinfo='percent+label',
                          pull=[0.05 if i == 0 else 0 for i in range(len(df_top))])
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to create donut chart: {e}")

def render_sunburst_chart_config(df):
    """Renders the UI for configuring a Sunburst Chart."""
    with st.container(border=True):
        st.write("**Select Data for Sunburst Chart**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if not numeric_cols or len(categorical_cols) < 1:
            st.warning("Sunburst Charts require at least one categorical (for path) and one numeric column (for values).")
            return

        st.multiselect("Hierarchy Path (from outer to inner):", options=categorical_cols, key='config_path_sunburst',
                       help="Select one or more categories to define the hierarchy. E.g., [team_name, player_name]")
        st.selectbox("Values (Size of Slices):", options=numeric_cols, key='config_values_sunburst')

def create_sunburst_chart_from_state(df):
    """Plots a sunburst chart using parameters stored in session_state."""
    path_cols = st.session_state.config_path_sunburst
    values_col = st.session_state.config_values_sunburst

    if not path_cols or not values_col:
        st.info("Please configure the Hierarchy Path and Values in the 'Configure Chart' tab.")
        return
    try:
        fig = px.sunburst(df, path=path_cols, values=values_col,
                          template="plotly_dark", title=f"Breakdown of {values_col} by {', '.join(path_cols)}")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to create sunburst chart: {e}")

def render_nightingale_chart_config(df):
    """Renders the UI for configuring a Nightingale Rose Chart."""
    with st.container(border=True):
        st.write("**Select Data for Nightingale Rose Chart**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if not numeric_cols or not categorical_cols:
            st.warning("Nightingale Charts require one categorical column (for slices) and one numeric column (for radius).")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Categories (Slices):", options=categorical_cols, key='config_theta_nightingale',
                         help="Each value in this column gets an equal-angled slice.")
        with col2:
            st.selectbox("Values (Radius of Slices):", options=numeric_cols, key='config_r_nightingale',
                         help="The value in this column determines how far each slice extends from the center.")

def create_nightingale_chart_from_state(df):
    """Plots a Nightingale Rose chart using parameters stored in session_state."""
    theta_col = st.session_state.config_theta_nightingale
    r_col = st.session_state.config_r_nightingale

    if not theta_col or not r_col:
        st.info("Please configure the Categories and Values in the 'Configure Chart' tab.")
        return
    try:
        # Using plotly.express with line_polar
        fig = px.bar_polar(df, r=r_col, theta=theta_col,
                           template="plotly_dark",
                           color=r_col, # Color bars by their value for a nice effect
                           title=f"Distribution of {r_col} by {theta_col}")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to create Nightingale Rose chart: {e}")

def render_scatter_plot_config(df):
    """Renders the UI for configuring a Scatter Plot."""
    with st.container(border=True):
        st.write("**1. Select Axes & Dimensions**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if len(numeric_cols) < 2:
            st.warning("Scatter Plots require at least two numeric columns.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("X-Axis (Numeric):", options=numeric_cols, key='config_x_col_scatter')
        with col2:
            st.selectbox("Y-Axis (Numeric):", options=numeric_cols, key='config_y_col_scatter',
                         index=min(1, len(numeric_cols) - 1))

        st.write("**2. Select Style (Optional)**")
        col3, col4 = st.columns(2)
        with col3:
            # This follows our smart UI pattern for colors
            summarize_is_on = st.session_state.get('scatter_plot_summarize_toggle', False)
            group_by_cols = st.session_state.get('scatter_plot_group_by_cols', [])
            valid_color_options = group_by_cols if summarize_is_on and group_by_cols else categorical_cols
            st.selectbox("Color by (Category):", options=[None] + valid_color_options, key='config_color_col_scatter')
        with col4:
            # This turns the scatter into a Bubble Chart
            st.selectbox("Size by (Numeric):", options=[None] + numeric_cols, key='config_size_col_scatter',
                         help="Turns the chart into a Bubble Chart.")

        st.selectbox("Add Trendline:", options=["None", "ols", "lowess"], key='config_trendline_scatter',
                     help="Draws a regression line. 'ols' is linear, 'lowess' is a smoothed line.")

def create_scatter_plot_from_state(df):
    """Plots a scatter chart using parameters stored in session_state."""
    x_col = st.session_state.config_x_col_scatter
    y_col = st.session_state.config_y_col_scatter

    if not x_col or not y_col:
        st.info("Please configure the X-Axis and Y-Axis in the 'Configure Chart' tab.")
        return

    try:
        # The trendline parameter expects None if the string is "None"
        trendline = st.session_state.config_trendline_scatter if st.session_state.config_trendline_scatter != "None" else None

        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=st.session_state.config_color_col_scatter,
            size=st.session_state.config_size_col_scatter,
            trendline=trendline,
            template="plotly_dark",
            title=f"{y_col} vs. {x_col}"
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to create scatter plot: {e}")

def render_histogram_config(df):
    """Renders the UI for configuring a Histogram."""
    with st.container(border=True):
        st.write("**1. Select Data**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if not numeric_cols:
            st.warning("Histograms require at least one numeric column.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Column to Analyze:", options=numeric_cols, key='config_x_col_hist')
        with col2:
            st.selectbox("Color by (Optional):", options=[None] + categorical_cols, key='config_color_col_hist',
                         help="Shows separate distributions for each category.")

        st.write("**2. Select Plot Type & Style**") # This replaces the old "Select Style" header
        st.radio(
            "Plot Type:",
            options=["Histogram", "Density (KDE)", "Cumulative (ECDF)"],
            key='config_hist_type',
            horizontal=True
        )

        if st.session_state.config_hist_type == 'Histogram':
            col3, col4 = st.columns(2)
            with col3:
                st.slider("Number of Bins:", min_value=5, max_value=100, key='config_nbins_hist',
                          help="Controls the granularity of the distribution.")
            with col4:
                if st.session_state.config_color_col_hist:  # Barmode only applies when color is used
                    st.radio("Bar Mode:", options=['overlay', 'stack'], key='config_barmode_hist',
                             help="Overlay shows transparent bars, Stack adds them up.")

def create_histogram_from_state(df):
    """Plots a histogram using parameters stored in session_state."""
    x_col = st.session_state.config_x_col_hist
    plot_type = st.session_state.config_hist_type

    if not x_col:
        st.info("Please select a column to analyze in the 'Configure Chart' tab.")
        return

    try:

        fig = None
        title = f"{plot_type} of {x_col}"
        color_col = st.session_state.config_color_col_hist

        if plot_type == "Histogram":
            # Barmode is only used if a color column is selected
            barmode = st.session_state.config_barmode_hist if st.session_state.config_color_col_hist else 'relative'

            fig = px.histogram(
                df,
                x=x_col,
                color=st.session_state.config_color_col_hist,
                nbins=st.session_state.config_nbins_hist,
                barmode=barmode,
                template="plotly_white",
                title=f"Distribution of {x_col}"
            )
            # Make overlayed histograms transparent so you can see both
            if barmode == 'overlay':
                fig.update_traces(opacity=0.75)
        elif plot_type == "Density (KDE)":
            # For KDE, we use density_heatmap and can show marginal histograms
            fig = px.density_heatmap(
                df, x=x_col, y=color_col,
                marginal_x="histogram", marginal_y="histogram" if color_col else None,
                template="plotly_white", title=title
            )

        elif plot_type == "Cumulative (ECDF)":
            fig = px.ecdf(
                df, x=x_col, color=color_col,
                template="plotly_white", title=title
            )
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to create histogram: {e}")

def render_box_plot_config(df):
    """Renders the UI for configuring a Box or Violin Plot."""
    with st.container(border=True):
        st.write("**1. Select Axes**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if not numeric_cols:
            st.warning("This chart requires at least one numeric column.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Value Axis (Numeric):", options=numeric_cols, key='config_y_col_box')
        with col2:
            st.selectbox("Category Axis (Optional):", options=[None] + categorical_cols, key='config_x_col_box',
                         help="Split the distribution by a category.")

        st.write("**2. Select Style**")
        col3, col4, col5 = st.columns(3)
        with col3:
            st.selectbox("Color by (Optional):", options=[None] + categorical_cols, key='config_color_col_box')
        with col4:
            st.radio("Plot Type:", options=['Box', 'Violin'], key='config_plot_type_box', horizontal=True)
        with col5:
            st.toggle("Show all data points", key='config_points_box',
                      help="Overlays all individual points on the plot.")

def create_box_plot_from_state(df):
    """Plots a Box or Violin chart using parameters stored in session_state."""
    y_col = st.session_state.config_y_col_box

    if not y_col:
        st.info("Please select a 'Value Axis' in the 'Configure Chart' tab.")
        return

    try:
        plot_type = st.session_state.config_plot_type_box
        points = "all" if st.session_state.config_points_box else False
        title = f"{plot_type} Plot of {y_col}"
        if st.session_state.config_x_col_box:
            title += f" by {st.session_state.config_x_col_box}"

        # Dynamically choose the plotting function
        if plot_type == 'Box':
            fig = px.box(
                df,
                y=y_col,
                x=st.session_state.config_x_col_box,
                color=st.session_state.config_color_col_box,
                points=points,
                template="plotly_white",
                title=title
            )
        else:  # Violin
            fig = px.violin(
                df,
                y=y_col,
                x=st.session_state.config_x_col_box,
                color=st.session_state.config_color_col_box,
                points=points,
                box=True,  # Show a mini box plot inside the violin
                template="plotly_white",
                title=title
            )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to create {plot_type.lower()} plot: {e}")

def render_heatmap_config(df):
    """Renders the UI for configuring a Heatmap."""
    with st.container(border=True):
        st.write("**1. Select Axes & Value**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if len(categorical_cols) < 2 or not numeric_cols:
            st.warning("Heatmaps require at least two categorical columns and one numeric column.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("X-Axis Category:", options=categorical_cols, key='config_x_col_heat')
        with col2:
            st.selectbox("Y-Axis Category:",
                         options=[c for c in categorical_cols if c != st.session_state.config_x_col_heat],
                         key='config_y_col_heat')
        with col3:
            st.selectbox("Color Value (Numeric):", options=numeric_cols, key='config_z_col_heat')

        st.write("**2. Select Style**")
        col4, col5 = st.columns(2)
        with col4:
            st.selectbox("Color Theme:", options=['Reds', 'Blues', 'Viridis', 'Plasma', 'YlGnBu'],
                         key='config_color_scale_heat')
        with col5:
            st.toggle("Show Values on Cells", value=True, key='config_text_auto_heat')

def create_heatmap_from_state(df):
    """Pivots data and plots a heatmap using parameters stored in session_state."""
    x_col = st.session_state.config_x_col_heat
    y_col = st.session_state.config_y_col_heat
    z_col = st.session_state.config_z_col_heat

    if not all([x_col, y_col, z_col]):
        st.info("Please configure the X-Axis, Y-Axis, and Color Value in the 'Configure Chart' tab.")
        return

    try:
        # A heatmap requires data in a "matrix" or "pivoted" format.
        # We use pandas' pivot_table to create this from our "long" data.
        heatmap_data = df.pivot_table(
            index=y_col,
            columns=x_col,
            values=z_col,
            aggfunc='mean'  # Default to mean for duplicate entries
        ).fillna(0)  # Fill any missing cells with 0

        fig = px.imshow(
            heatmap_data,
            text_auto=st.session_state.config_text_auto_heat,
            aspect="auto",
            template="plotly_white",
            color_continuous_scale=st.session_state.config_color_scale_heat,
            title=f"{z_col} by {y_col} and {x_col}"
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to create heatmap: {e}. Heatmaps require a specific data structure.")

def render_radar_chart_config(df):
    """Renders the UI for configuring a Radar Chart."""
    with st.container(border=True):
        st.write("**Configure Your Radar Chart**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if not numeric_cols or not categorical_cols:
            st.warning("Radar Charts require at least one categorical and multiple numeric columns.")
            return

        st.info("A Radar Chart is best for comparing a few items across multiple metrics.")

        # 1. Select the column that contains the items you want to compare
        item_col = st.selectbox("Select column with items to compare:", options=categorical_cols,
                                key='config_item_col_radar')

        if item_col:
            # 2. Select which specific items from that column you want to plot
            all_items = df[item_col].unique()
            st.multiselect("Select items to show (3-5 recommended):", options=all_items, key='config_items_radar')

        # 3. Select the numeric metrics for the radar's axes
        st.multiselect("Select metrics for axes:", options=numeric_cols, key='config_metrics_radar')

        st.toggle(
            "Normalize Data (0-100 Score)",
            key='config_normalize_radar',
            help="Rescales all metrics to a common 0-100 scale to make profiles comparable. Highly recommended if your metrics have different ranges (e.g., runs and average)."
        ) \
            # In scripts/chart_generator.py

def create_radar_chart_from_state(df):
    """
    Plots a robust radar chart using plotly.graph_objects for full control,
    especially over the hover tooltip.
    """
    item_col = st.session_state.get('config_item_col_radar')
    items_to_plot = st.session_state.get('config_items_radar', [])
    metrics_to_plot = st.session_state.get('config_metrics_radar', [])
    normalize = st.session_state.get('config_normalize_radar', False)

    if not all([item_col, items_to_plot]) or len(metrics_to_plot) < 2:
        st.info(
            "From the 'Configure Chart' tab, please select an 'item column', at least 2 'items to show', and at least 2 'metrics for axes'.")
        return

    try:
        # --- Data Preparation ---
        # 1. Filter to only the selected players/items
        df_filtered = df[df[item_col].isin(items_to_plot)].set_index(item_col)

        # 2. Select only the metrics we need
        df_metrics = df_filtered[metrics_to_plot]

        # 3. Prepare data for normalization (find min/max for each metric across the selected items)
        data_stats = {
            'min': df_metrics.min(),
            'max': df_metrics.max()
        }

        # --- Chart Creation using plotly.graph_objects ---
        fig = go.Figure()

        # Add one trace (one player shape) at a time
        for item in items_to_plot:
            player_data = df_metrics.loc[item]

            # Get the raw values for the hover tooltip
            raw_values = player_data.values

            # Get the normalized values for plotting the shape
            if normalize:
                # Min-Max normalization: (value - min) / (max - min)
                # This calculation is now done per-player, per-metric
                normalized_values = [
                    ((raw_values[i] - data_stats['min'][metric]) / (
                                data_stats['max'][metric] - data_stats['min'][metric])) * 100
                    if (data_stats['max'][metric] - data_stats['min'][metric]) != 0 else 0
                    for i, metric in enumerate(metrics_to_plot)
                ]
                plot_values = normalized_values
            else:
                plot_values = raw_values

            hover_text_lines = [f"<b>{item}</b>"]
            hover_text_lines.extend([
                f"{metric}: {raw_values[i]:.2f}"
                for i, metric in enumerate(metrics_to_plot)
            ])
            final_hover_text = "<br>".join(hover_text_lines)
            fig.add_trace(go.Scatterpolar(
                r=plot_values,
                theta=metrics_to_plot,
                fill='toself',
                name=item,  # The player's name appears in the legend
                text=final_hover_text,  # Use our new complete text block
                hoverinfo="text"  # Tell plotly to ONLY use our custom text
            ))

        # --- Styling ---
        radial_axis_title = "Normalized Score (0-100)" if normalize else "Raw Value"
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    # If normalizing, set the range to 0-100 for a clean look
                    range=[0, 100] if normalize else None,
                    title=dict(text=radial_axis_title)
                )
            ),
            showlegend=True,
            template="plotly_dark",
            title=f"Profile Comparison: {', '.join(items_to_plot)}"
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(
            f"Failed to create radar chart. This chart requires at least 2 metrics and 2 items to compare. Error: {e}")

def render_treemap_config(df):
    """Renders the UI for configuring a Treemap."""
    with st.container(border=True):
        st.write("**Configure Your Treemap**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if not numeric_cols or not categorical_cols:
            st.warning("Treemaps require at least one numeric and one categorical column.")
            return

        st.info(
            "A Treemap shows hierarchical data. Start by selecting the top-level category for the 'path', then add more for deeper levels.")

        col1, col2 = st.columns(2)
        with col1:
            st.multiselect("Hierarchy Path (Categories):", options=categorical_cols, key='config_path_treemap',
                           help="Defines the nested levels of the treemap.")
        with col2:
            st.selectbox("Size of Rectangles (Numeric):", options=numeric_cols, key='config_values_treemap')

        st.selectbox("Color of Rectangles (Optional Numeric):", options=[None] + numeric_cols,
                     key='config_color_treemap',
                     help="Use color to represent a second numeric metric, like 'strike_rate'.")

def create_treemap_from_state(df):
    """Plots a treemap using parameters stored in session_state."""
    path = st.session_state.config_path_treemap
    values = st.session_state.config_values_treemap
    color = st.session_state.config_color_treemap

    if not path or not values:
        st.info("Please configure the Hierarchy Path and Size in the 'Configure Chart' tab.")
        return

    try:
        title = f"Treemap of {values} by {', '.join(path)}"
        if color:
            title += f" (Colored by {color})"

        fig = px.treemap(
            df,
            path=[px.Constant("All")] + path,  # Add a root node for a better starting view
            values=values,
            color=color,
            color_continuous_scale='YlGnBu',  # A nice blue-green color scale
            template="plotly_white",
            title=title,
            hover_data={col: ':.2f' for col in [values, color] if col}  # Format hover data
        )
        fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to create treemap. Error: {e}")

def render_sankey_diagram_config(df):
    """Renders the UI for configuring a Sankey Diagram."""
    with st.container(border=True):
        st.write("**Configure Your Sankey Diagram**")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'int64']).columns.tolist()

        if len(categorical_cols) < 2 or not numeric_cols:
            st.warning(
                "Sankey Diagrams require at least two categorical columns (for Source and Target) and one numeric column (for Value).")
            return

        st.info(
            "Select the columns representing the 'Source' of the flow, the 'Target', and the numeric 'Value' of the flow.")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.selectbox("Source (From):", options=categorical_cols, key='config_source_sankey')
        with col2:
            st.selectbox("Target (To):",
                         options=[c for c in categorical_cols if c != st.session_state.config_source_sankey],
                         key='config_target_sankey')
        with col3:
            st.selectbox("Value (Flow Amount):", options=numeric_cols, key='config_value_sankey')

def create_sankey_diagram_from_state(df):
    """Prepares data and plots a Sankey diagram using parameters from session_state."""
    source_col = st.session_state.config_source_sankey
    target_col = st.session_state.config_target_sankey
    value_col = st.session_state.config_value_sankey

    if not all([source_col, target_col, value_col]):
        st.info("Please configure the Source, Target, and Value in the 'Configure Chart' tab.")
        return

    try:
        # --- Data Preparation for Sankey ---
        # 1. Create a complete list of unique labels from both source and target columns
        labels = pd.concat([df[source_col], df[target_col]]).unique()

        # 2. Create a mapping from the label name to its integer index
        label_map = {label: i for i, label in enumerate(labels)}

        # 3. Create the final source, target, and value lists for the plot
        source_indices = df[source_col].map(label_map)
        target_indices = df[target_col].map(label_map)
        values = df[value_col]

        # --- Plotting with plotly.graph_objects ---
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values
            )
        )])

        fig.update_layout(
            title_text=f"Flow from {source_col} to {target_col}",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(
            f"Failed to create Sankey diagram. Ensure your data structure is suitable (Source -> Target -> Value). Error: {e}")

# ----- UNUSED -----
def create_scatter_plot(df, n_cols, c_cols):
    st.write(f"#### Scatter Plot: {n_cols[1]} vs. {n_cols[0]}")
    fig = px.scatter(df, x=n_cols[0], y=n_cols[1], hover_name=c_cols[0] if c_cols else None,
                     color=c_cols[0] if c_cols else None, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


def create_pie_chart(df, n_cols, c_cols):
    st.write(f"#### Pie Chart: Distribution of {n_cols[0]}")
    top_n_df = df.nlargest(10, n_cols[0])
    fig = px.pie(top_n_df, names=c_cols[0], values=n_cols[0], hole=0.4, template="plotly_dark")
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)


def create_bubble_chart(df, n_cols, c_cols):
    st.write(f"#### Bubble Chart: {n_cols[1]} vs. {n_cols[0]}, Sized by {n_cols[2]}")
    fig = px.scatter(df, x=n_cols[0], y=n_cols[1], size=n_cols[2], color=c_cols[0] if c_cols else None,
                     hover_name=c_cols[0] if c_cols else None, template="plotly_dark", size_max=60)
    st.plotly_chart(fig, use_container_width=True)


# --- Distribution Charts ---
def create_histogram(df, n_cols, c_cols):
    st.write(f"#### Histogram: Distribution of {n_cols[0]}")
    fig = px.histogram(df, x=n_cols[0], color=c_cols[0] if c_cols else None, nbins=30, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


def create_box_plot(df, n_cols, c_cols):
    st.write(f"#### Box Plot: Distribution of {n_cols[0]}")
    fig = px.box(df, y=n_cols[0], x=c_cols[0] if c_cols else None, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


def create_violin_plot(df, n_cols, c_cols):
    st.write(f"#### Violin Plot: Distribution of {n_cols[0]}")
    fig = px.violin(df, y=n_cols[0], x=c_cols[0] if c_cols else None, box=True, points="all", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


# --- Hierarchical Charts ---
def create_treemap(df, n_cols, c_cols):
    st.write(f"#### Treemap: {n_cols[0]} by {c_cols[0]}")
    fig = px.treemap(df, path=[px.Constant("All")] + c_cols, values=n_cols[0], template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


def create_sunburst_chart(df, n_cols, c_cols):
    st.write(f"#### Sunburst Chart: {n_cols[0]} by {c_cols[0]}")
    fig = px.sunburst(df, path=c_cols, values=n_cols[0], template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


# --- Relational / Flow Charts ---
def create_heatmap(df, n_cols, c_cols):
    st.write(f"#### Heatmap: {n_cols[0]} by {c_cols[0]} and {c_cols[1]}")
    heatmap_data = df.pivot_table(index=c_cols[0], columns=c_cols[1], values=n_cols[0], aggfunc='mean').fillna(0)
    fig = px.imshow(heatmap_data, text_auto=True, aspect="auto", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


def create_radar_chart(df, n_cols, c_cols):
    st.write(f"#### Radar Chart: Player Comparison")
    # Radar charts are best for comparing entities across multiple metrics
    fig = px.line_polar(df, r=n_cols[0], theta=c_cols[0], line_close=True, template="plotly_dark")
    fig.update_traces(fill='toself')
    st.plotly_chart(fig, use_container_width=True)


def create_sankey_diagram(df, n_cols, c_cols):
    st.write(f"#### Sankey Diagram: Flow Analysis")
    source_col, target_col = c_cols[0], c_cols[1]
    value_col = n_cols[0]

    # Create a list of unique labels for nodes
    labels = list(pd.concat([df[source_col], df[target_col]]).unique())

    # Create dictionaries to map labels to integer indices
    source_map = {label: i for i, label in enumerate(labels)}

    # Create the Sankey trace
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels
        ),
        link=dict(
            source=[source_map[s] for s in df[source_col]],
            target=[source_map[t] for t in df[target_col]],
            value=df[value_col]
        )
    )])
    fig.update_layout(title_text=f"Flow from {source_col} to {target_col}", font_size=10)
    st.plotly_chart(fig, use_container_width=True)


def create_funnel_chart(df, n_cols, c_cols):
    st.write(f"#### Funnel Chart: Stages of {c_cols[0]}")
    fig = px.funnel(df, x=n_cols[0], y=c_cols[0], template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
# UTILITY FUNCTION
# ==============================================================================
def clean_dataframe(df):
    """Performs standard cleaning and type conversion."""
    df_clean = df.copy()
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            converted_col = pd.to_numeric(df_clean[col], errors='coerce')
            if not converted_col.isnull().all():
                df_clean[col] = converted_col
    return df_clean