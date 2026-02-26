import streamlit as st
import pandas as pd
import mysql.connector
import os
import altair as alt

st.set_page_config(layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# -------- DATABASE LOAD -------- #

@st.cache_data(ttl=60)
def load_data():
    conn = mysql.connector.connect(
    host=st.secrets["db"]["host"],
    port=st.secrets["db"]["port"],
    user=st.secrets["db"]["user"],
    password=st.secrets["db"]["password"],
    database=st.secrets["db"]["database"]
)
    
    
    query = """
    SELECT 
    booking_id,
    booking_datetime,
    booking_status,
    vehicle_type,
    booking_value,
    ride_distance_km,
    driver_ratings,
    customer_rating,
    payment_method,
    incomplete_rides_reason,
    customer_id
    FROM ola
    """

    df = pd.read_sql(query, conn)

    conn.close()

    # 🔥 FIX OBJECT TO FLOAT
    df['driver_ratings'] = pd.to_numeric(df['driver_ratings'], errors='coerce')
    df['customer_rating'] = pd.to_numeric(df['customer_rating'], errors='coerce')
    df['booking_value'] = pd.to_numeric(df['booking_value'], errors='coerce')
    df['ride_distance_km'] = pd.to_numeric(df['ride_distance_km'], errors='coerce')
    df['booking_datetime'] = pd.to_datetime(df['booking_datetime'], errors='coerce')
    return df

df = load_data()

# -------- CSS -------- #

st.markdown("""
<style>
/* SIDEBAR BUTTON STYLE */
[data-testid="stButton"] > button {
    display:flex !important;
    align-items:center !important;
    justify-content:flex-start !important;
    gap:20px !important;
    background-color:#2a2a2a !important;
    color:white !important;
    border:none !important;
    padding:30px 70px !important;
    border-radius:12px !important;
    margin-bottom:12px !important;
    text-align:left !important;
    width:120% !important;
    font-size:30px !important;
}

[data-testid="stButton"] > button:hover {
    background-color:#8BC34A !important;
    color:black !important;
}

/* CENTER TABLE */
.center-table {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
}

/* TABLE STYLE */
.center-table table {
    width: 70% !important;
    font-size: 20px !important;
    border-collapse: collapse !important;
}

.center-table th {
    text-align: center !important;
    padding: 12px !important;
}

.center-table td {
    text-align: center !important;
    padding: 12px !important;
}

</style>
""", unsafe_allow_html=True)


# -------- SESSION -------- #

if "menu" not in st.session_state:
    st.session_state.menu = "Overall"

# -------- SIDEBAR -------- #

with st.sidebar:

    col1,col2 = st.columns([1,3])

    with col1:
        st.image(os.path.join(BASE_DIR,"logo.png"), width=90)

    with col2:
        st.image(os.path.join(BASE_DIR,"ola_text.png"), width=150)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📊 Overall"):
        st.session_state.menu="Overall"

    if st.button("🚗 Vehicle Type"):
        st.session_state.menu="Vehicle Type"

    if st.button("₹ Revenue"):
        st.session_state.menu="Revenue"

    if st.button("🚘 Cancellation"):
        st.session_state.menu="Cancellation"

    if st.button("⭐ Ratings"):
        st.session_state.menu="Ratings"

# -------- MAIN AREA -------- #

if st.session_state.menu == "Overall":
    
    st.markdown("## 📊 Overall Ride Overview")

    # -------- KPI CARDS -------- #

    total_rides = df.shape[0]
    success_rides = df[df['booking_status']=="Success"].shape[0]
    cancelled_rides = df[df['booking_status']!="Success"].shape[0]
    success_rate = (success_rides/total_rides)*100

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total Rides", total_rides)
    col2.metric("Successful Rides", success_rides)
    col3.metric("Cancelled Rides", cancelled_rides)
    col4.metric("Success Rate (%)", f"{success_rate:.2f}")

    st.markdown("---")

    # -------- RIDE VOLUME OVER TIME -------- #

    ride_volume = df.groupby(df['booking_datetime'].dt.date).size().reset_index(name='Ride_Count')

    st.subheader("Ride Volume Over Time")

    st.line_chart(
        ride_volume.set_index('booking_datetime')
    )

    st.markdown("---")

    # -------- BOOKING STATUS BREAKDOWN -------- #

    status_breakdown = df['booking_status'].value_counts().reset_index()
    status_breakdown.columns = ['Booking Status','Count']

    st.subheader("Booking Status Breakdown")

    st.bar_chart(
        status_breakdown.set_index('Booking Status')
    )

 #   --------- Vechile TYPE ----------------#

elif st.session_state.menu == "Vehicle Type":
    
    st.markdown("## 🚗 Vehicle Type Summary")

    vehicle_summary = df.groupby('vehicle_type').agg(
        Total_Booking_Value=('booking_value','sum'),
        Successful_Booking_Value=('booking_value',
            lambda x: x[df.loc[x.index,'booking_status']=="Success"].sum()),
        Avg_Distance_Travelled=('ride_distance_km','mean'),
        Total_Distance_Travelled=('ride_distance_km','sum')
    ).reset_index().round(2)

    
    vehicle_summary['vehicle_type_clean'] = (
        vehicle_summary['vehicle_type']
        .astype(str)
        .str.replace('\xa0','',regex=True)
        .str.strip()
        .str.lower()
    )

    vehicle_icons = {
        "prime sedan": "https://img.icons8.com/color/48/car--v1.png",
        "prime suv": "https://img.icons8.com/color/48/suv.png",
        "prime plus": "https://img.icons8.com/color/48/limousine.png",
        "mini": "https://img.icons8.com/color/48/van.png",
        "bike": "https://img.icons8.com/color/48/motorcycle.png",
        "auto": "https://img.icons8.com/external-flaticons-lineal-color-flat-icons/64/external-auto-rickshaw-transportation-flaticons-lineal-color-flat-icons.png",
        "ebike": "https://img.icons8.com/color/48/scooter.png"
    }

    vehicle_summary['Icon'] = vehicle_summary['vehicle_type_clean'].map(vehicle_icons)

    vehicle_summary['Icon'] = vehicle_summary['Icon'].fillna(
        "https://img.icons8.com/color/48/car.png"
    )

    vehicle_summary['Icon'] = vehicle_summary['Icon'].apply(
        lambda x: f'<img src="{x}" width="45">'
    )
    
    vehicle_summary = vehicle_summary.rename(columns={
    "vehicle_type": "Vehicle Type",
    "Total_Booking_Value": "Total Booking Value",
    "Successful_Booking_Value": "Successful Booking Value",
    "Avg_Distance_Travelled": "Avg Distance Travelled",
    "Total_Distance_Travelled": "Total Distance Travelled"})

    vehicle_summary = vehicle_summary[
    ['Icon','Vehicle Type',
     'Total Booking Value',
     'Successful Booking Value',
     'Avg Distance Travelled',
     'Total Distance Travelled']
]

    st.markdown(
        f"""
        <div class="center-table">
            {vehicle_summary.to_html(escape=False,index=False)}
        </div>
        """,
        unsafe_allow_html=True
    )

elif st.session_state.menu == "Revenue":
    
    st.markdown("## 💰 Revenue Insights")

    # -------- REVENUE BY PAYMENT METHOD -------- #

    revenue_payment = df.groupby('payment_method')['booking_value'].sum().reset_index()

    st.subheader("Revenue by Payment Method")

    st.bar_chart(
        revenue_payment.set_index('payment_method')
    )

    st.markdown("---")

    # -------- TOP 5 CUSTOMERS -------- #

    top_customers = df.groupby('customer_id')['booking_value'].sum().reset_index()

    top_customers = top_customers.sort_values(
        by='booking_value',
        ascending=False
    ).head(5)

    st.subheader("Top 5 Customers by Total Booking Value")

    st.bar_chart(
        top_customers.set_index('customer_id')
    )

    st.markdown("---")

    # -------- DISTANCE DISTRIBUTION PER DAY -------- #

    df['booking_day'] = df['booking_datetime'].dt.date

    distance_daily = df.groupby('booking_day')['ride_distance_km'].sum().reset_index()

    st.subheader("Ride Distance Distribution Per Day")

    st.line_chart(
        distance_daily.set_index('booking_day')
    )

         #------------ CANCELLATION -------------#

elif st.session_state.menu == "Cancellation":
    
    st.markdown("## 🚘 Cancellation Insights")

    # -------- FILTER ONLY CANCELLED -------- #

    cancel_df = df[
        (df['booking_status']!="Success") &
        (df['incomplete_rides_reason']!="Not Applicable")
    ]

    # -------- CLASSIFY TYPE -------- #

    def classify_reason(x):
        if x == "Upgrading Vehicle Type":
            return "Customer"
        else:
            return "Driver"

    cancel_df['Cancellation_Type'] = cancel_df['incomplete_rides_reason'].apply(classify_reason)

    total_cancelled = cancel_df.shape[0]
    customer_cancel = cancel_df[cancel_df['Cancellation_Type']=="Customer"].shape[0]
    driver_cancel = cancel_df[cancel_df['Cancellation_Type']=="Driver"].shape[0]

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Cancelled Rides", total_cancelled)
    col2.metric("Customer Cancelled", customer_cancel)
    col3.metric("Driver Cancelled", driver_cancel)

    st.markdown("---")

    # -------- DRIVER REASONS -------- #

    import altair as alt

    driver_reason = cancel_df[
        cancel_df['Cancellation_Type']=="Driver"
    ]['incomplete_rides_reason'].value_counts().reset_index()

    driver_reason.columns = ['Driver Reason','Count']

    st.subheader("Driver Cancellation Reasons")

    chart = alt.Chart(driver_reason).mark_bar().encode(
        x=alt.X('Count:Q'),
        y=alt.Y('Driver Reason:N', sort='-x')
    ).properties(width=600, height=300)

    st.altair_chart(chart)

    st.markdown("---")

    # -------- CUSTOMER VS DRIVER SPLIT -------- #

    cancel_split = pd.DataFrame({
        "Type": ["Customer", "Driver"],
        "Count": [customer_cancel, driver_cancel]
    })

    st.subheader("Cancellation Type Split")

    pie = alt.Chart(cancel_split).mark_arc().encode(
        theta="Count",
        color="Type"
    )

    st.altair_chart(pie)



# -------- RATINGS VIEW -------- #

elif st.session_state.menu == "Ratings":

    st.markdown("## ⭐ Vehicle Ratings Summary")

    rating_summary = df.groupby('vehicle_type').agg(
        Avg_Driver_Rating=('driver_ratings','mean'),
        Avg_Customer_Rating=('customer_rating','mean')
    ).reset_index().round(2)

    # NORMALIZE VEHICLE TYPE
    rating_summary['vehicle_type_clean'] = rating_summary['vehicle_type'].str.lower().str.strip()

    # ICON MAP
    vehicle_icons = {
        "prime sedan": "https://img.icons8.com/color/48/car--v1.png",
        "prime suv": "https://img.icons8.com/color/48/suv.png",
        "prime plus": "https://img.icons8.com/color/48/limousine.png",
        "mini": "https://img.icons8.com/color/48/van.png",
        "bike": "https://img.icons8.com/color/48/motorcycle.png",
        "auto": "https://img.icons8.com/external-flaticons-lineal-color-flat-icons/64/external-auto-rickshaw-transportation-flaticons-lineal-color-flat-icons.png",
        "ebike": "https://img.icons8.com/color/48/scooter.png"
    }

    rating_summary['Icon'] = rating_summary['vehicle_type_clean'].map(vehicle_icons)

    rating_summary['Icon'] = rating_summary['Icon'].fillna(
        "https://img.icons8.com/color/48/car.png"
    )

    rating_summary['Icon'] = rating_summary['Icon'].apply(
        lambda x: f'<img src="{x}" width="45">'
    )

    rating_summary = rating_summary[
        ['Icon','vehicle_type','Avg_Driver_Rating','Avg_Customer_Rating']
    ]

    st.markdown(
    f"""
    <div class="center-table">
        {rating_summary.to_html(escape=False,index=False)}
    </div>
    """,
    unsafe_allow_html=True
)
