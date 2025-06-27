import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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


def generate_visualizations(df):
    """
    Displays a UI for the user to select and configure charts.
    """
    df_clean = clean_dataframe(df)
    if df_clean.empty:
        st.info("The query returned no data to visualize.")
        return

    st.subheader("Chart Studio")

    chart_type = st.selectbox(
        "Choose a chart type to build:",
        options=["Bar Chart", "Line Chart", "Pie/Donut Chart", "Scatter Plot", "Bubble Chart", "Histogram", "Tree Map", "Sunburst Chart", "Heat Map", "Radar Chart", "Sankey Chart", "Funnel Chart"]
    )

    if chart_type == "Bar Chart":
        build_bar_chart(df_clean)


# ==============================================================================
# 3. INDIVIDUAL PLOTTING FUNCTIONS
# Each function creates one type of chart.
# ==============================================================================

# --- Standard Charts ---

def build_bar_chart(df):
    """
    Displays a UI for building a customized bar chart, with an option to aggregate data.
    """
    st.write("---")
    st.write("### Bar Chart Options")

    # 1. Analyze dataframe to find column types
    all_cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

    df_to_plot = df.copy()

    with st.expander("Filter Data (Optional)"):
        # Initialize a session state variable to store active filters
        if 'active_filters' not in st.session_state:
            st.session_state.active_filters = {}

        # UI to add a new filter
        st.write("**Add a new filter:**")
        col_to_filter = st.selectbox("Select column to filter:", options=df.columns, index=None,
                                     placeholder="Choose a column")

        if col_to_filter:
            if df[col_to_filter].dtype == 'object':
                unique_vals = df[col_to_filter].unique()
                selected_vals = st.multiselect(f"Select values for '{col_to_filter}':", options=unique_vals)
                if st.button(f"Apply filter on '{col_to_filter}'"):
                    st.session_state.active_filters[col_to_filter] = selected_vals
                    st.rerun()  # Rerun to apply the filter immediately

            elif pd.api.types.is_numeric_dtype(df[col_to_filter]) and df[col_to_filter].nunique() > 1:
                min_val, max_val = float(df[col_to_filter].min()), float(df[col_to_filter].max())
                slider_range = st.slider(f"Select range for '{col_to_filter}':", min_val, max_val, (min_val, max_val))
                if st.button(f"Apply filter on '{col_to_filter}'"):
                    st.session_state.active_filters[col_to_filter] = slider_range
                    st.rerun()

        # Display active filters and allow their removal
        if st.session_state.active_filters:
            st.write("**Active Filters:**")
            for col, val in st.session_state.active_filters.items():
                if st.button(f"{col} = {str(val)[:30]}... ❌", key=f"del_{col}"):
                    del st.session_state.active_filters[col]
                    st.rerun()

    # Apply the stored filters to the dataframe
    for col, val in st.session_state.active_filters.items():
        if df_to_plot[col].dtype == 'object':
            df_to_plot = df_to_plot[df_to_plot[col].isin(val)]
        else:  # Numeric
            df_to_plot = df_to_plot[df_to_plot[col].between(val[0], val[1])]

    if not numeric_cols or not categorical_cols:
        st.warning("To build a Bar Chart, your data needs at least one numeric column and one categorical column.")
        return

    df_to_plot = df  # By default, use the original detailed dataframe

    # --- NEW TAB-BASED UI FOR A CLEANER LOOK ---
    tab1, tab2 = st.tabs(["📊 Configure Chart", "⚙️ Summarize Data (Optional)"])

    with tab1:
        st.write("**Chart Axes & Style**")
        plot_categorical_cols = df_to_plot.select_dtypes(include=['object']).columns.tolist()
        plot_numeric_cols = df_to_plot.select_dtypes(include=['number']).columns.tolist()

        if not plot_numeric_cols or not plot_categorical_cols:
            st.warning("Not enough data to plot after filtering.")
            return

        # Let user select value columns first
        value_cols = st.multiselect("Value Axis (Numeric):", options=plot_numeric_cols,
                                    default=plot_numeric_cols[0] if plot_numeric_cols else [])

        col1, col2 = st.columns(2)
        with col1:
            category_col = st.selectbox("Category Axis (Text):", options=plot_categorical_cols)
        with col2:
            color_col = st.selectbox("Color by:", options=[None] + plot_categorical_cols)

        orientation = st.radio("Orientation:", ["Horizontal", "Vertical"], horizontal=True, index=0)
        barmode = st.radio("Bar Mode:", ['group', 'stack'], horizontal=True,
                           help="Only applies if you select multiple 'Value' columns.")

    with tab2:
        st.write("**Aggregation Options**")
        summarize_toggle = st.toggle("Enable Summarization", value=False)

        group_by_cols = []
        agg_functions = {}

        if summarize_toggle:
            group_by_cols = st.multiselect("Group By:", options=plot_categorical_cols)

            if group_by_cols:
                st.write("**Define Aggregation for Selected Value Columns:**")
                # FEATURE 2: ONLY show aggregation options for the columns selected in the "Value Axis"
                for col in value_cols:
                    agg_choice = st.selectbox(f"Aggregation for '{col}':",
                                              options=['Sum', 'Mean', 'Max', 'Min', 'Count'], key=f"agg_{col}")
                    agg_functions[col] = agg_choice.lower()

                # Perform aggregation
                try:
                    # Select only the columns needed for grouping and aggregation
                    cols_to_agg = group_by_cols + value_cols
                    df_agg = df_to_plot[cols_to_agg]
                    df_to_plot = df_agg.groupby(group_by_cols).agg(agg_functions).reset_index()
                except Exception as e:
                    st.error(f"Failed to group data. Error: {e}")
                    return

    # --- Plotting (uses the final state of df_to_plot) ---
    if category_col and value_cols:
        try:
            # Re-sort data for better presentation after potential aggregation
            sort_col = value_cols[0]
            if sort_col in df_to_plot.columns:
                df_to_plot = df_to_plot.sort_values(by=sort_col, ascending=(orientation == "Horizontal"))

            x_axis, y_axis = (category_col, value_cols) if orientation == "Vertical" else (value_cols, category_col)

            fig = px.bar(df_to_plot, x=x_axis, y=y_axis, color=color_col,
                         title=f"{', '.join(value_cols)} by {category_col}",
                         template="plotly_white", barmode=barmode,
                         orientation='v' if orientation == 'Vertical' else 'h')

            legend_title = ", ".join(value_cols)
            fig.update_layout(legend_title_text=legend_title)

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to create chart. Error: {e}")


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