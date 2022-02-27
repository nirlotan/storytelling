from re import X
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import altair as alt

from google.oauth2 import service_account
from gsheetsdb import connect


# Create a connection object.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
    ],
)
conn = connect(credentials=credentials)

# Perform SQL query on the Google Sheet.
# Uses st.cache to only rerun when the query changes or after 10 min.
@st.cache(allow_output_mutation=True, show_spinner=False, hash_funcs={pd.DataFrame: hash})
def run_query(query):
    rows = conn.execute(query, headers=1)
    return rows

def conv(x):
    try:
        return int(x)
    except:
        return 0

def dt_convert( dt ):
    return f"{dt.year}.{dt.month}"

sheet_url = st.secrets["private_gsheets_url"]
rows = run_query(f'SELECT * FROM "{sheet_url}"')
main_df = pd.DataFrame(rows)

# main_df = load_data()

df = main_df.copy()
df.views = df.views.apply(conv)
df.Month = df.Month.apply(dt_convert)

text_input_container = st.empty()
pwd = text_input_container.text_input("Password:",type='password')

if pwd == st.secrets["password"]:
    text_input_container.empty()
    selected_platforms = st.sidebar.multiselect("Platform:",
                                                df['Platform'].unique(),
                                                df['Platform'].unique())

    selected_months = st.sidebar.multiselect("Months:",
                                                df['Month'].unique(),
                                                df['Month'].unique())

    selected_topics = st.sidebar.multiselect("Topics:",
                                                df['topic'].unique(),
                                                df['topic'].unique())

    st.title("Intel Storyteller's Annual Report")


    report = st.selectbox("Report", ['Dashboard','Annual Summary','Monthly Interactions'])

    df = df[(df["Platform"].isin(selected_platforms))&
            (df["Month"].isin(selected_months))&
            (df["topic"].isin(selected_topics))]
    group_df = df.groupby(by=['Month','Platform','topic']).sum().reset_index()

    if report == "Dashboard":

        slicer = st.selectbox("Slice by:", ['','Platform','topic'])


        if slicer != '':

            base_chart = alt.Chart(group_df).mark_bar().encode(
                x = alt.X("Month"),
                color=slicer
            ).properties(
                width=300,
                height=200
            ).interactive()

        else:    
            base_chart = alt.Chart(group_df).mark_bar().encode(
                x = alt.X("Month")
            ).properties(
                width=300,
                height=200
            ).interactive()


        base_chart.encode(y=alt.Y("comments"),tooltip="comments").properties(title="comments") | \
                            base_chart.encode(y=alt.Y("views"),tooltip="views").properties(title="views")


                            
        base_chart.encode(y=alt.Y("shares"),tooltip="shares").properties(title="comments") | \
                            base_chart.encode(y=alt.Y("interactions"),tooltip="interactions").properties(title="interactions")
                            

    elif report == "Annual Summary":
        
        gdf = pd.melt(df, id_vars=['Author','topic'], value_vars=['likes',
       'comments', 'shares', 'interactions', 'views'])
        
        all_selection = st.checkbox('Select all authors', value=True)

        if all_selection:
            selected_authors = df['Author'].unique().tolist()
        else:
            exp = st.expander("Select Users:")
            selected_authors = exp.multiselect("Authors:",
                                                    df['Author'].unique().tolist())


        a_s_filter = st.multiselect("Filter:",
                                    df.topic.unique(),
                                    df.topic.unique())

        gdf = gdf[(gdf["Author"].isin(selected_authors))&(gdf["topic"].isin(a_s_filter))]
        
        bars = alt.Chart(gdf).mark_bar().encode(

            x='sum(value):Q',
            y='variable:O',
            color='topic:N',
        #    column='חודש:N',
            tooltip=['sum(value)']
        )
        
        text = bars.mark_text(
                        align='left',
                        baseline='middle',
                        dx=3  # Nudges text to right so it doesn't appear on top of the bar
                    ).encode(
                        text='sum(value):Q'
                    )
        a_s = (bars + text).properties(height=400)
        
        st.altair_chart(a_s,use_container_width=True)



    