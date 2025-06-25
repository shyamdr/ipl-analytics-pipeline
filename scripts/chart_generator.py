import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def generate_visualizations(df_original):
    """
    Analyzes a DataFrame, intelligently cleans it by converting types
    without deleting essential categorical columns, and generates charts.
    """
    if df_original.empty:
        st.info("The query returned no data to visualize.")
        return

    st.subheader("Visualizations")

    # --- NEW AND IMPROVED: INTELLIGENT DATA CONVERSION ---
    # Work on a copy to avoid changing the original dataframe
    df = df_original.copy()

    # Loop through each column to check and convert its type
    for col in df.columns:
        # We only care about columns that are currently of 'object' type
        if df[col].dtype == 'object':
            # Attempt to convert this column to a numeric type.
            # 'coerce' will replace any text that can't be converted (like player names) with an error value (NaN).
            converted_col = pd.to_numeric(df[col], errors='coerce')

            # **This is the crucial check:**
            # If NOT ALL values were turned into errors (i.e., the conversion was successful for at least one value),
            # then we replace the original text column with the new numeric one.
            # Otherwise, we leave the original text column as is (e.g., for 'player_name').
            if not converted_col.isnull().all():
                df[col] = converted_col

    # --- END OF THE NEW LOGIC ---

    # Helper functions to check cleaned data types
    def is_numeric(series):
        return pd.api.types.is_numeric_dtype(series)

    def is_categorical(series):
        # We now consider object columns as our primary categorical columns
        return pd.api.types.is_object_dtype(series) or pd.api.types.is_categorical_dtype(series)

    num_cols = len(df.columns)

    # Find all categorical and numeric columns after cleaning
    categorical_cols = [col for col in df.columns if is_categorical(df[col])]
    numeric_cols = [col for col in df.columns if is_numeric(df[col])]

    if categorical_cols and numeric_cols:
        # We have what we need for a bar chart!
        # Let's use the first identified categorical and numeric columns.
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]

        st.write(f"#### Bar Chart: {num_col} by {cat_col}")

        CATEGORY_LIMIT = 20
        TOP_N = 10

        # Set the categorical column as the index for plotting
        plot_df = df.set_index(cat_col)

        if len(plot_df.index.unique()) > CATEGORY_LIMIT:
            st.info(f"The data contains too many categories. Displaying the Top {TOP_N} results sorted by '{num_col}'.")

            # Sort the dataframe by the numeric column and take the top N
            top_n_df = plot_df.sort_values(by=num_col, ascending=False).head(TOP_N)
            st.bar_chart(top_n_df[[num_col]])
        else:
            # If within the limit, sort it for better readability anyway
            sorted_df = plot_df.sort_values(by=num_col, ascending=False)
            st.bar_chart(sorted_df[[num_col]])

    elif num_cols == 2 and not categorical_cols and len(numeric_cols) == 2:
        # Handle case for line charts (two numeric columns)
        st.write(f"#### Line Chart: {numeric_cols[1]} vs. {numeric_cols[0]}")
        st.line_chart(df.set_index(numeric_cols[0]))

    else:
        st.info("Could not automatically determine a suitable chart for this data.")