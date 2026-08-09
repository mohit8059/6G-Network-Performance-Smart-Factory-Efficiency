import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="6G Smart Factory Analytics", page_icon="🏭", layout="wide")
st.title("🏭 6G Network Impact on Manufacturing Efficiency")
st.markdown("**Strategic Analytics for Thales Group | Industry 4.0 & 5.0 Environments**")
st.markdown("---")

file_path = "Thales_Group_Manufacturing.csv"

if not os.path.exists(file_path):
    st.error(f"❌ Error: Dataset '{file_path}' not found! Please upload it to your directory.")
    st.stop()

# --- DATA INGESTION & ENGINEERING ---
@st.cache_data
def load_and_preprocess():
    df = pd.read_csv(file_path)
    
    # Create DateTime
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Timestamp'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    
    # Feature Engineering: Network Quality Classification
    # Assuming lower latency and packet loss is better
    lat_median = df['Network_Latency_ms'].median()
    loss_median = df['Packet_Loss_%'].median()
    
    def classify_network(row):
        if row['Network_Latency_ms'] < lat_median and row['Packet_Loss_%'] < loss_median:
            return 'High (Stable)'
        elif row['Network_Latency_ms'] > lat_median * 1.5 or row['Packet_Loss_%'] > loss_median * 1.5:
            return 'Low (Unstable)'
        else:
            return 'Medium'
            
    df['Network_Quality'] = df.apply(classify_network, axis=1)
    
    # Feature Engineering: Network Stability Index (0-100 scale, higher is better)
    max_lat = df['Network_Latency_ms'].max()
    max_loss = df['Packet_Loss_%'].max()
    df['Network_Stability_Index'] = 100 - (((df['Network_Latency_ms']/max_lat)*50) + ((df['Packet_Loss_%']/max_loss)*50))
    
    return df

df = load_and_preprocess()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🎛️ Diagnostics Controls")

# Operation Mode Filter
op_modes = ["All"] + list(df['Operation_Mode'].unique())
selected_mode = st.sidebar.selectbox("Select Operation Mode", op_modes)

# Efficiency Status Filter
eff_status = ["All"] + list(df['Efficiency_Status'].unique())
selected_eff = st.sidebar.selectbox("Efficiency Class", eff_status)

# Network Quality Filter
net_quality = ["All"] + list(df['Network_Quality'].unique())
selected_net = st.sidebar.selectbox("Network Quality Band", net_quality)

# Apply Filters
filtered_df = df.copy()
if selected_mode != "All":
    filtered_df = filtered_df[filtered_df['Operation_Mode'] == selected_mode]
if selected_eff != "All":
    filtered_df = filtered_df[filtered_df['Efficiency_Status'] == selected_eff]
if selected_net != "All":
    filtered_df = filtered_df[filtered_df['Network_Quality'] == selected_net]

# Subsample for faster plotting if dataset is too large
plot_df = filtered_df.sample(min(5000, len(filtered_df)), random_state=42)

# --- EXECUTIVE KPIs ---
st.subheader("📊 Network & Production KPIs")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Network Latency", f"{filtered_df['Network_Latency_ms'].mean():.2f} ms")
col2.metric("Avg Packet Loss", f"{filtered_df['Packet_Loss_%'].mean():.2f} %")
col3.metric("Network Stability Index", f"{filtered_df['Network_Stability_Index'].mean():.1f} / 100")
col4.metric("Avg Defect Rate", f"{filtered_df['Quality_Control_Defect_Rate_%'].mean():.2f} %")
st.markdown("---")

# --- DASHBOARD MODULES (TABS) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Network Overview", 
    "⚙️ Network vs Efficiency", 
    "🚨 Quality & Error Impact", 
    "💡 6G Optimization Insights"
])

# TAB 1: Network Performance Overview
with tab1:
    st.subheader("Latency & Packet Loss Distribution")
    c1, c2 = st.columns(2)
    with c1:
        fig_lat = px.histogram(plot_df, x="Network_Latency_ms", color="Network_Quality", 
                               title="Latency Distribution across Quality Bands",
                               labels={"Network_Latency_ms": "Latency (ms)"})
        st.plotly_chart(fig_lat, use_container_width=True)
    with c2:
        fig_loss = px.box(plot_df, x="Network_Quality", y="Packet_Loss_%", color="Network_Quality",
                          title="Packet Loss Variations")
        st.plotly_chart(fig_loss, use_container_width=True)

# TAB 2: Network vs Efficiency Dashboard
with tab2:
    st.subheader("Efficiency Distribution by Network Quality")
    eff_dist = filtered_df.groupby(['Network_Quality', 'Efficiency_Status']).size().reset_index(name='Count')
    fig_eff = px.bar(eff_dist, x="Network_Quality", y="Count", color="Efficiency_Status", barmode="group",
                     title="How Network Instability Shifts Efficiency Profiles")
    st.plotly_chart(fig_eff, use_container_width=True)

    st.subheader("Latency Impact on Production Speed")
    fig_scatter1 = px.scatter(plot_df, x="Network_Latency_ms", y="Production_Speed_units_per_hr", 
                              color="Efficiency_Status", opacity=0.6,
                              title="Production Speed Sensitivity to Latency Zones",
                              labels={"Production_Speed_units_per_hr": "Production Speed (Units/hr)"})
    st.plotly_chart(fig_scatter1, use_container_width=True)

# TAB 3: Quality & Error Impact Panel
with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Error Rate vs Packet Loss")
        fig_err = px.scatter(plot_df, x="Packet_Loss_%", y="Error_Rate_%", color="Operation_Mode", trendline="ols",
                             title="Operational Errors Driven by Packet Drops")
        st.plotly_chart(fig_err, use_container_width=True)
    with c2:
        st.subheader("Defect Rate under Varying Networks")
        # Purana code hata kar yeh naya daal do
    fig_def = px.density_contour(plot_df, x="Network_Latency_ms", y="Quality_Control_Defect_Rate_%",
                             title="Defect Concentration Zones")
    fig_def.update_traces(contours_coloring="fill")
    st.plotly_chart(fig_def, use_container_width=True)

# TAB 4: 6G Optimization Insights
with tab4:
    st.subheader("Strategic Diagnostics & Tolerances")
    
    # Calculate thresholds dynamically
    crit_lat = plot_df[plot_df['Efficiency_Status'] == 'Low']['Network_Latency_ms'].median()
    crit_loss = plot_df[plot_df['Efficiency_Status'] == 'Low']['Packet_Loss_%'].median()
    
    st.error(f"⚠️ **Latency Risk Zone:** Efficiency drops significantly when 6G latency exceeds **{crit_lat:.2f} ms**.")
    st.warning(f"⚠️ **Packet Loss Risk Zone:** Defect rates and errors spike when packet loss exceeds **{crit_loss:.2f} %**.")
    st.success("✅ **Recommendation:** Prioritize 6G network slicing protocols for high-load 'Active' machine states to guarantee sub-millisecond latencies, preventing ghost-errors and ensuring high efficiency output.")
    
    st.markdown("---")
    st.markdown("### Operation Mode Sensitivity")
    mode_impact = plot_df.groupby('Operation_Mode')[['Network_Latency_ms', 'Error_Rate_%']].mean().reset_index()
    fig_mode = px.bar(mode_impact, x='Operation_Mode', y='Error_Rate_%', color='Network_Latency_ms',
                      title="Average Error Rate per Mode (Colored by Latency Exposure)",
                      labels={'Error_Rate_%': 'Avg Error Rate (%)'})
    st.plotly_chart(fig_mode, use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>Developed by Mohit Kasana | End-to-End Analytics Portfolio</p>", unsafe_allow_html=True)