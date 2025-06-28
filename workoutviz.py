import re
import pandas as pd
import numpy as np
import matplotlib as plt
import plotly.express as px
import streamlit as st


st.set_page_config(layout="wide", page_title="Dashboard")
st.title(":muscle: Strong App Workout Dashboard")

# UI Layout
col1, col2, col3 = st.columns(3)
st.sidebar.write("## About! :gear:")
my_upload = st.sidebar.file_uploader("Upload your exported data", type=["csv"])
st.sidebar.write("This dashboard visualizes your workout data from the mobile app 'Strong'.")
st.sidebar.write('''
To export your data from the app, click the 'Profile' :bust_in_silhouette: tab at the bottom left, then tap the Gear :gear: icon at the top left.
Scroll down and select 'Export Strong Data'. 
''')


if my_upload is None:
    st.write("Upload your data to get started!")
else:
    try:
        df = pd.read_csv(my_upload)
        # st.write(df.head())

        df = df[~(df["Set Order"] == 'Rest Timer')] # removing records related to rest between sets

        df['Date'] = pd.to_datetime(df['Date'])
        df.sort_values(by='Date', inplace=True)
        df['Day'] = df.apply(lambda row : row['Date'].date(), axis=1)
        df['Month'] = df.apply(lambda row : row['Date'].month_name(), axis=1)


        def convert_duration_to_minutes(duration_str):
            """
            Converts a time duration string (e.g., '1hr 3', '4m', '2hr') into total minutes.

            Args:
                duration_str: The input string representing the time duration.

            Returns:
                The total duration in minutes as an integer. Returns None if the format
                is invalid or ambiguous.
            """
            total_minutes = 0
            duration_str = duration_str.strip().lower() # Normalize input

            # Regular expression to find all number-unit pairs
            # It captures:
            # 1. The number (e.g., '1', '30')
            # 2. The unit (e.g., 'hr', 'm', 'hour', 'minute', or empty if just a number)
            # This pattern tries to match explicit units first
            matches = re.findall(r'(\d+)\s*(?:hr|hour|hours|h)?\s*(\d*)\s*(?:m|min|minute|minutes)?', duration_str)

            # Simplified approach:
            # Find all numerical parts and their corresponding unit.
            # Look for patterns like "NUMBER UNIT" or just "NUMBER"
            # Example: "1hr 3m", "2h 15", "30", "5 minutes"
            hour_match = re.search(r'(\d+)\s*(?:hr|hour|hours|h)', duration_str)
            minute_match = re.search(r'(\d+)\s*(?:m|min|minute|minutes)', duration_str)

            if hour_match:
                total_minutes += int(hour_match.group(1)) * 60

            if minute_match:
                total_minutes += int(minute_match.group(1))
            elif not hour_match:
                # If no hour unit was explicitly found, and no minute unit was explicitly found,
                # check if there's a standalone number. This covers '4m' (which would be caught
                # by minute_match) AND '10' (meaning 10 minutes).
                # We need to be careful not to double count from '1hr 3' where '3' is also a number.

                # If there's no explicit hour or minute unit, but a single number, assume minutes
                single_number_match = re.fullmatch(r'(\d+)', duration_str)
                if single_number_match:
                    total_minutes = int(single_number_match.group(1)) # Overwrite if it was 0
                    return total_minutes # Direct return for single number minute cases
            else:
                # Handle "1hr 3" case: If an hour was found, check for a trailing number without units
                # and assume it's minutes.
                # This regex looks for: (number) (hour unit) (optional space) (number at end)
                trailing_minutes_match = re.search(r'(\d+)\s*(?:hr|hour|hours|h)\s*(\d+)$', duration_str)
                if trailing_minutes_match:
                    # Check if the number captured by trailing_minutes_match.group(2)
                    # wasn't already part of an explicit minute match.
                    # In this scenario, it wouldn't be because we are in the 'else' block for minute_match.
                    total_minutes += int(trailing_minutes_match.group(2))

            # Final check: If nothing was parsed, return None.
            # This specifically addresses cases like "invalid string"
            if total_minutes == 0 and not (hour_match or minute_match or re.fullmatch(r'\d+', duration_str)):
                return None

            return total_minutes


        df['Duration'] = df.apply(lambda row: convert_duration_to_minutes(row['Duration']), axis=1)


        # ## Key Performance Metrics

        TOTAL_WORKOUTS = len(df['Day'].unique())
        WORKOUT_TYPES = df['Workout Name'].unique()
        BEST_MONTH = df['Month'].mode()[0] # most workouts in a month
        BEST_MONTH_COUNT = len(df[df.Month == BEST_MONTH].groupby(['Day']))
        AVG_DURATION = df['Duration'].mean()
        LONGEST_WORKOUT = df['Duration'].max()

        col1.metric(label=":hash: Total Workout Days", value=f"{TOTAL_WORKOUTS}")
        col2.metric(label=":date: Best Month", value=f"{BEST_MONTH}({BEST_MONTH_COUNT} days)")
        col3.metric(label=":stopwatch: Avg Workout Length", value=f"{AVG_DURATION:,.0f} mins")

        df['Volume'] = df['Weight'] * df['Reps']

        st.write("### :trophy: Personal Records")
        st.write("Calculated by best total volume for a set (weight x reps)")
        st.write(df.groupby(['Exercise Name'])['Volume'].max())

        st.write("### :chart_with_upwards_trend: Progress")

        fig1 = px.line(df, x="Day", y="Weight", title='Workout Weight over Time', color='Exercise Name', markers=True, template='plotly_dark')
        fig1.update_traces(textposition="bottom right")
        st.plotly_chart(fig1)


        fig2 = px.box(df, x="Month", y="Weight", title="Monthly Weight Progression by Exercise", color="Exercise Name", notched=False, template="plotly_dark")
        st.plotly_chart(fig2)

        fig3 = px.box(df, x="Month", y="Duration", title="Workout Durations", color="Workout Name", notched=False, template="plotly_dark")
        st.plotly_chart(fig3)
    except Exception as e:
        st.error(str(e))




