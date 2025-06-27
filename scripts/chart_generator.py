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
        'summarize_toggle': False,
        'group_by_cols': [],
        'config_category_col': None,
        'config_value_cols': [],
        'config_color_col': None,
        'config_orientation': 'Horizontal',
        'config_barmode': 'group'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==============================================================================
# 1. CHART ELIGIBILITY CHECKER
# This function checks the dataframe and returns a list of all possible charts.
# ==============================================================================
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
        options=["Bar Chart", "Line Chart", "Pie Chart"],
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
        # Other chart configs would go here

    with tab_summary:
        # Pass df_clean so the Group By dropdown has all categorical columns
        render_summary_tab(df_clean)

        # --- PROCESS THE DATA *AFTER* ALL UI WIDGETS HAVE BEEN RENDERED ---
    # This ensures we use the most up-to-date selections from session_state
    df_processed = process_data(df_clean)

    # --- RENDER THE PLOT PREVIEW using the correctly processed data ---
    st.write("---")
    st.write("### Chart Preview")

    if st.session_state.chart_type == 'Bar Chart':
        create_bar_chart_from_state(df_processed)
    # elif st.session_state.chart_type == 'Line Chart':
    #     create_line_chart_from_state(df_processed)


def process_data(df):
    """
    Applies filtering and aggregation based on session state.
    Returns the processed dataframe.
    """
    df_processed = df.copy()

    # 1. Apply filters
    for col, val in st.session_state.get('active_filters', {}).items():
        if col in df_processed.columns:
            if df_processed[col].dtype == 'object':
                df_processed = df_processed[df_processed[col].isin(val)]
            else:
                df_processed = df_processed[df_processed[col].between(val[0], val[1])]

    # 2. Apply summarization
    if st.session_state.get('summarize_toggle') and st.session_state.get('group_by_cols'):
        try:
            # Get aggregation functions for only the selected value columns
            agg_functions = {
                col: st.session_state[f'agg_{col}']
                for col in st.session_state.config_value_cols
                if f'agg_{col}' in st.session_state
            }
            if agg_functions:
                df_processed = df_processed.groupby(st.session_state.group_by_cols).agg(agg_functions).reset_index()
        except Exception as e:
            st.error(f"Failed to group data: {e}")

    return df_processed


def render_filter_tab(df):
    """Renders the UI for the Filter Data tab."""
    with st.container(border=True):
        st.write("**Add a new filter:**")
        col_to_filter = st.selectbox("Column to filter:", options=df.columns, index=None, placeholder="Choose a column",
                                     key="col_filter_select")

        if col_to_filter:
            # Filter definition UI... (This logic remains the same as before)
            if df[col_to_filter].dtype == 'object':
                unique_vals = df[col_to_filter].unique()
                selected_vals = st.multiselect(f"Values for '{col_to_filter}':", options=unique_vals,
                                               key=f"filter_val_{col_to_filter}")
                if st.button("Apply Filter", key=f"apply_{col_to_filter}"):
                    st.session_state.active_filters[col_to_filter] = selected_vals
                    #st.rerun()
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
                    #del st.session_state.active_filters[col]
                    #st.rerun()


def render_summary_tab(df):
    """Renders the UI for the Summarize Data tab."""
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.toggle("Enable Summarization", key='summarize_toggle')

        if st.session_state.summarize_toggle:
            with col2:
                st.multiselect("Group By:", options=df.select_dtypes(include=['object']).columns, key='group_by_cols')

            if st.session_state.group_by_cols and st.session_state.config_value_cols:
                st.write("**Define Aggregation for Selected Value Columns:**")
                agg_cols = st.columns(len(st.session_state.config_value_cols))
                for i, col in enumerate(st.session_state.config_value_cols):
                    with agg_cols[i]:
                        st.selectbox(f"Agg for '{col}':", options=['sum', 'mean', 'max', 'min', 'count'],
                                     key=f"agg_{col}")


def render_bar_chart_config(df):
    """Renders the UI for configuring a Bar Chart."""
    with st.container(border=True):
        st.write("**1. Select Axes**")
        plot_numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        plot_categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

        col1, col2 = st.columns(2)
        with col1:
            st.selectbox("Category Axis (Text):", options=plot_categorical_cols, key='config_category_col')
        with col2:
            st.multiselect("Value Axis (Numeric):", options=plot_numeric_cols, key='config_value_cols')

        st.write("**2. Select Style**")
        col3, col4, col5 = st.columns(3)
        with col3:
            st.selectbox("Color by:", options=[None] + plot_categorical_cols, key='config_color_col')
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

    # ... The rest of your plotting logic from px.bar onwards ...
    # This function would be very similar to the plotting part of the old build_bar_chart
    try:
        df_sorted = df.sort_values(by=value_cols[0], ascending=(st.session_state.config_orientation == "Horizontal"))
        x_axis, y_axis = (category_col, value_cols) if st.session_state.config_orientation == "Vertical" else (
        value_cols, category_col)

        fig = px.bar(df_sorted, x=x_axis, y=y_axis, color=st.session_state.config_color_col,
                     title=f"{', '.join(value_cols)} by {category_col}", template="plotly_white",
                     barmode=st.session_state.config_barmode,
                     orientation='v' if st.session_state.config_orientation == 'Vertical' else 'h')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to create chart: {e}")


def create_line_chart(df, n_cols, c_cols):
    st.write(f"#### Line Chart: {n_cols[0]} over {c_cols[0] if c_cols else 'Index'}")
    x_axis = c_cols[0] if c_cols else df.index
    df_sorted = df.sort_values(by=x_axis)
    fig = px.line(df_sorted, x=x_axis, y=n_cols[0], template="plotly_white", markers=True)
    st.plotly_chart(fig, use_container_width=True)


def create_scatter_plot(df, n_cols, c_cols):
    st.write(f"#### Scatter Plot: {n_cols[1]} vs. {n_cols[0]}")
    fig = px.scatter(df, x=n_cols[0], y=n_cols[1], hover_name=c_cols[0] if c_cols else None,
                     color=c_cols[0] if c_cols else None, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


def create_pie_chart(df, n_cols, c_cols):
    st.write(f"#### Pie Chart: Distribution of {n_cols[0]}")
    top_n_df = df.nlargest(10, n_cols[0])
    fig = px.pie(top_n_df, names=c_cols[0], values=n_cols[0], hole=0.4, template="plotly_white")
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)


def create_bubble_chart(df, n_cols, c_cols):
    st.write(f"#### Bubble Chart: {n_cols[1]} vs. {n_cols[0]}, Sized by {n_cols[2]}")
    fig = px.scatter(df, x=n_cols[0], y=n_cols[1], size=n_cols[2], color=c_cols[0] if c_cols else None,
                     hover_name=c_cols[0] if c_cols else None, template="plotly_white", size_max=60)
    st.plotly_chart(fig, use_container_width=True)


# --- Distribution Charts ---
def create_histogram(df, n_cols, c_cols):
    st.write(f"#### Histogram: Distribution of {n_cols[0]}")
    fig = px.histogram(df, x=n_cols[0], color=c_cols[0] if c_cols else None, nbins=30, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


def create_box_plot(df, n_cols, c_cols):
    st.write(f"#### Box Plot: Distribution of {n_cols[0]}")
    fig = px.box(df, y=n_cols[0], x=c_cols[0] if c_cols else None, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


def create_violin_plot(df, n_cols, c_cols):
    st.write(f"#### Violin Plot: Distribution of {n_cols[0]}")
    fig = px.violin(df, y=n_cols[0], x=c_cols[0] if c_cols else None, box=True, points="all", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


# --- Hierarchical Charts ---
def create_treemap(df, n_cols, c_cols):
    st.write(f"#### Treemap: {n_cols[0]} by {c_cols[0]}")
    fig = px.treemap(df, path=[px.Constant("All")] + c_cols, values=n_cols[0], template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


def create_sunburst_chart(df, n_cols, c_cols):
    st.write(f"#### Sunburst Chart: {n_cols[0]} by {c_cols[0]}")
    fig = px.sunburst(df, path=c_cols, values=n_cols[0], template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


# --- Relational / Flow Charts ---
def create_heatmap(df, n_cols, c_cols):
    st.write(f"#### Heatmap: {n_cols[0]} by {c_cols[0]} and {c_cols[1]}")
    heatmap_data = df.pivot_table(index=c_cols[0], columns=c_cols[1], values=n_cols[0], aggfunc='mean').fillna(0)
    fig = px.imshow(heatmap_data, text_auto=True, aspect="auto", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


def create_radar_chart(df, n_cols, c_cols):
    st.write(f"#### Radar Chart: Player Comparison")
    # Radar charts are best for comparing entities across multiple metrics
    fig = px.line_polar(df, r=n_cols[0], theta=c_cols[0], line_close=True, template="plotly_white")
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
    fig = px.funnel(df, x=n_cols[0], y=c_cols[0], template="plotly_white")
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