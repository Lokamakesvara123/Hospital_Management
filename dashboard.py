import streamlit as st
import os

st.set_page_config(page_title="MedCare Hospital Dashboard", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    [data-testid="stSidebar"] {
        background-color: #1a1a2e;
    }
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }
    .header-container {
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px 0;
        border-bottom: 2px solid #00d4aa;
        margin-bottom: 20px;
    }
    .hospital-name {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00d4aa;
        margin: 0;
    }
    .hospital-tagline {
        font-size: 0.9rem;
        color: #a0a0a0;
        margin: 0;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(0, 212, 170, 0.3);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    .kpi-card-green {
        background: linear-gradient(135deg, #0d4e3a 0%, #1a7a5c 100%);
        border: 1px solid rgba(0, 255, 136, 0.3);
    }
    .kpi-card-purple {
        background: linear-gradient(135deg, #2d1b69 0%, #5b3a9e 100%);
        border: 1px solid rgba(167, 139, 250, 0.3);
    }
    .kpi-card-orange {
        background: linear-gradient(135deg, #4a2c0a 0%, #b85c1e 100%);
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    .kpi-icon {
        font-size: 2rem;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 5px 0;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #b0b0b0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))
session = conn.session()

session.sql("USE DATABASE HOSPITAL_MANAGE_DB").collect()
session.sql("USE SCHEMA HOSPITAL_SCHEMA").collect()

st.markdown("""
<div class="header-container">
    <img src="https://img.icons8.com/3d-fluency/94/hospital.png" width="55"/>
    <div>
        <p class="hospital-name">MedCare Multi-Speciality Hospital</p>
        <p class="hospital-tagline">Advanced Healthcare Management System</p>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Navigation")
    page = st.radio(
        "Navigation",
        ["Overview", "Appointments", "Billing", "Patients", "Predictive Analytics"],
        label_visibility="collapsed"
    )
    st.divider()
    st.subheader("Filters")
    departments = session.sql("SELECT DISTINCT DEPARTMENT FROM FACT_APPOINTMENTS ORDER BY DEPARTMENT").to_pandas()
    dept_list = ["All"] + departments["DEPARTMENT"].tolist()
    selected_dept = st.selectbox("Department", dept_list)
    statuses = ["All", "Scheduled", "Completed", "No-Show", "Cancelled"]
    selected_status = st.selectbox("Status", statuses)
    st.divider()
    st.caption("MedCare Hospital v1.0")

dept_filter = "" if selected_dept == "All" else f" AND DEPARTMENT = '{selected_dept}'"
status_filter = "" if selected_status == "All" else f" AND STATUS = '{selected_status}'"

if page == "Overview":
    patients = session.sql("SELECT COUNT(DISTINCT PATIENT_ID) AS CNT FROM FACT_APPOINTMENTS").to_pandas()
    appointments = session.sql(f"SELECT COUNT(*) AS CNT FROM FACT_APPOINTMENTS WHERE 1=1{dept_filter}{status_filter}").to_pandas()
    billing = session.sql(f"SELECT COALESCE(SUM(NET_AMOUNT), 0) AS TOTAL FROM FACT_BILLING WHERE 1=1{dept_filter}").to_pandas()
    doctors = session.sql("SELECT COUNT(*) AS CNT FROM DIM_DOCTORS").to_pandas()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div class="kpi-value">{int(patients["CNT"][0])}</div>
            <div class="kpi-label">Total Patients</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-green">
            <div class="kpi-icon">🩺</div>
            <div class="kpi-value">{int(doctors["CNT"][0])}</div>
            <div class="kpi-label">Total Doctors</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-purple">
            <div class="kpi-icon">📋</div>
            <div class="kpi-value">{int(appointments["CNT"][0])}</div>
            <div class="kpi-label">Appointments</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card kpi-card-orange">
            <div class="kpi-icon">💰</div>
            <div class="kpi-value">₹{float(billing['TOTAL'][0]):,.0f}</div>
            <div class="kpi-label">Total Revenue</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Appointments by Department")
            dept_appt = session.sql(
                f"SELECT DEPARTMENT, COUNT(*) AS TOTAL FROM FACT_APPOINTMENTS WHERE 1=1{status_filter} GROUP BY DEPARTMENT ORDER BY TOTAL DESC"
            ).to_pandas()
            st.bar_chart(dept_appt, x="DEPARTMENT", y="TOTAL")

    with col2:
        with st.container(border=True):
            st.subheader("Revenue by Department")
            dept_rev = session.sql(
                "SELECT DEPARTMENT, SUM(NET_AMOUNT) AS TOTAL_REVENUE FROM FACT_BILLING GROUP BY DEPARTMENT ORDER BY TOTAL_REVENUE DESC"
            ).to_pandas()
            st.bar_chart(dept_rev, x="DEPARTMENT", y="TOTAL_REVENUE")

    with st.container(border=True):
        st.subheader("Daily OPD Trend")
        daily_trend = session.sql(
            f"SELECT APPT_DATE, COUNT(*) AS TOTAL_VISITS FROM FACT_APPOINTMENTS WHERE 1=1{dept_filter}{status_filter} GROUP BY APPT_DATE ORDER BY APPT_DATE"
        ).to_pandas()
        st.line_chart(daily_trend, x="APPT_DATE", y="TOTAL_VISITS")

elif page == "Appointments":
    total_appt = session.sql(f"SELECT COUNT(*) AS CNT FROM FACT_APPOINTMENTS WHERE 1=1{dept_filter}{status_filter}").to_pandas()
    completed = session.sql(f"SELECT COUNT(*) AS CNT FROM FACT_APPOINTMENTS WHERE STATUS='Completed'{dept_filter}").to_pandas()
    noshow = session.sql(f"SELECT COUNT(*) AS CNT FROM FACT_APPOINTMENTS WHERE STATUS='No-Show'{dept_filter}").to_pandas()
    cancelled = session.sql(f"SELECT COUNT(*) AS CNT FROM FACT_APPOINTMENTS WHERE STATUS='Cancelled'{dept_filter}").to_pandas()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">📋</div>
            <div class="kpi-value">{int(total_appt["CNT"][0])}</div>
            <div class="kpi-label">Total Appointments</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-green">
            <div class="kpi-icon">✅</div>
            <div class="kpi-value">{int(completed["CNT"][0])}</div>
            <div class="kpi-label">Completed</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-orange">
            <div class="kpi-icon">⚠️</div>
            <div class="kpi-value">{int(noshow["CNT"][0])}</div>
            <div class="kpi-label">No-Show</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card kpi-card-purple">
            <div class="kpi-icon">❌</div>
            <div class="kpi-value">{int(cancelled["CNT"][0])}</div>
            <div class="kpi-label">Cancelled</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Status Breakdown")
            status_data = session.sql(
                f"SELECT STATUS, COUNT(*) AS CNT FROM FACT_APPOINTMENTS WHERE 1=1{dept_filter} GROUP BY STATUS"
            ).to_pandas()
            st.bar_chart(status_data, x="STATUS", y="CNT")

    with col2:
        with st.container(border=True):
            st.subheader("Top Departments")
            top_dept = session.sql(
                f"SELECT DEPARTMENT, COUNT(*) AS CNT FROM FACT_APPOINTMENTS WHERE 1=1{status_filter} GROUP BY DEPARTMENT ORDER BY CNT DESC LIMIT 5"
            ).to_pandas()
            st.bar_chart(top_dept, x="DEPARTMENT", y="CNT")

    with st.container(border=True):
        st.subheader("Appointment Records")
        appt_data = session.sql(
            f"SELECT APPT_ID, APPT_DATE, PATIENT_ID, DOCTOR_ID, DEPARTMENT, SLOT, STATUS FROM FACT_APPOINTMENTS WHERE 1=1{dept_filter}{status_filter} ORDER BY APPT_DATE DESC LIMIT 50"
        ).to_pandas()
        st.dataframe(appt_data, use_container_width=True, hide_index=True)

elif page == "Billing":
    billing_total = session.sql(f"SELECT COALESCE(SUM(NET_AMOUNT),0) AS NET, COALESCE(SUM(GROSS_AMOUNT),0) AS GROSS, COALESCE(SUM(DISCOUNT_AMOUNT),0) AS DISCOUNT, COALESCE(SUM(TAX_AMOUNT),0) AS TAX, COUNT(*) AS BILLS FROM FACT_BILLING WHERE 1=1{dept_filter}").to_pandas()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card kpi-card-green">
            <div class="kpi-icon">💵</div>
            <div class="kpi-value">₹{float(billing_total['GROSS'][0]):,.0f}</div>
            <div class="kpi-label">Gross Amount</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-orange">
            <div class="kpi-icon">🏷️</div>
            <div class="kpi-value">₹{float(billing_total['DISCOUNT'][0]):,.0f}</div>
            <div class="kpi-label">Discount</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-purple">
            <div class="kpi-icon">🧾</div>
            <div class="kpi-value">₹{float(billing_total['TAX'][0]):,.0f}</div>
            <div class="kpi-label">Tax Collected</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">💰</div>
            <div class="kpi-value">₹{float(billing_total['NET'][0]):,.0f}</div>
            <div class="kpi-label">Net Revenue</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Payment Mode")
            payment = session.sql(
                f"SELECT PAYMENT_MODE, COUNT(*) AS CNT FROM FACT_BILLING WHERE 1=1{dept_filter} GROUP BY PAYMENT_MODE ORDER BY CNT DESC"
            ).to_pandas()
            st.bar_chart(payment, x="PAYMENT_MODE", y="CNT")

    with col2:
        with st.container(border=True):
            st.subheader("Revenue by Department")
            rev_dept = session.sql(
                "SELECT DEPARTMENT, SUM(NET_AMOUNT) AS REVENUE FROM FACT_BILLING GROUP BY DEPARTMENT ORDER BY REVENUE DESC"
            ).to_pandas()
            st.bar_chart(rev_dept, x="DEPARTMENT", y="REVENUE")

    with st.container(border=True):
        st.subheader("Billing Records")
        bill_data = session.sql(
            f"SELECT BILL_ID, BILL_DATE, PATIENT_ID, DEPARTMENT, SERVICE_DESC, NET_AMOUNT, PAYMENT_MODE, INSURER_NAME FROM FACT_BILLING WHERE 1=1{dept_filter} ORDER BY BILL_DATE DESC LIMIT 50"
        ).to_pandas()
        st.dataframe(bill_data, use_container_width=True, hide_index=True)

elif page == "Patients":
    patient_stats = session.sql("SELECT COUNT(DISTINCT PATIENT_ID) AS TOTAL, COUNT(DISTINCT DEPARTMENT) AS DEPTS FROM FACT_APPOINTMENTS").to_pandas()
    avg_visits = session.sql("SELECT ROUND(AVG(CNT),1) AS AVG_VISITS FROM (SELECT PATIENT_ID, COUNT(*) AS CNT FROM FACT_APPOINTMENTS GROUP BY PATIENT_ID)").to_pandas()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">👥</div>
            <div class="kpi-value">{int(patient_stats["TOTAL"][0])}</div>
            <div class="kpi-label">Total Patients</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-green">
            <div class="kpi-icon">🏥</div>
            <div class="kpi-value">{int(patient_stats["DEPTS"][0])}</div>
            <div class="kpi-label">Departments</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-purple">
            <div class="kpi-icon">📊</div>
            <div class="kpi-value">{float(avg_visits["AVG_VISITS"][0])}</div>
            <div class="kpi-label">Avg Visits/Patient</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Patients by Department")
            pat_dept = session.sql("SELECT DEPARTMENT, COUNT(DISTINCT PATIENT_ID) AS CNT FROM FACT_APPOINTMENTS GROUP BY DEPARTMENT ORDER BY CNT DESC").to_pandas()
            st.bar_chart(pat_dept, x="DEPARTMENT", y="CNT")

    with col2:
        with st.container(border=True):
            st.subheader("Patients by Status")
            pat_status = session.sql("SELECT STATUS, COUNT(DISTINCT PATIENT_ID) AS CNT FROM FACT_APPOINTMENTS GROUP BY STATUS").to_pandas()
            st.bar_chart(pat_status, x="STATUS", y="CNT")

    with st.container(border=True):
        st.subheader("Patient Appointment History")
        patient_data = session.sql(
            "SELECT PATIENT_ID, COUNT(*) AS TOTAL_VISITS, MIN(APPT_DATE) AS FIRST_VISIT, MAX(APPT_DATE) AS LAST_VISIT FROM FACT_APPOINTMENTS GROUP BY PATIENT_ID ORDER BY TOTAL_VISITS DESC LIMIT 50"
        ).to_pandas()
        st.dataframe(patient_data, use_container_width=True, hide_index=True)

elif page == "Predictive Analytics":
    import pandas as pd

    st.markdown("""
    <div class="kpi-card" style="margin-bottom:20px; text-align:left; padding:25px;">
        <div style="font-size:1.5rem; font-weight:700; color:#00d4aa;">🔮 Predictive Analytics</div>
        <div style="color:#b0b0b0; margin-top:5px;">AI-powered insights & forecasting based on historical hospital data</div>
    </div>""", unsafe_allow_html=True)

    daily_data = session.sql(
        "SELECT APPT_DATE, COUNT(*) AS VISITS FROM FACT_APPOINTMENTS GROUP BY APPT_DATE ORDER BY APPT_DATE"
    ).to_pandas()
    daily_data["APPT_DATE"] = pd.to_datetime(daily_data["APPT_DATE"])

    dept_trend = session.sql(
        "SELECT DEPARTMENT, APPT_DATE, COUNT(*) AS CNT FROM FACT_APPOINTMENTS GROUP BY DEPARTMENT, APPT_DATE ORDER BY DEPARTMENT, APPT_DATE"
    ).to_pandas()

    noshow_rate = session.sql(
        "SELECT DEPARTMENT, ROUND(SUM(CASE WHEN STATUS='No-Show' THEN 1 ELSE 0 END)*100.0/COUNT(*), 1) AS NOSHOW_RATE, COUNT(*) AS TOTAL FROM FACT_APPOINTMENTS GROUP BY DEPARTMENT ORDER BY NOSHOW_RATE DESC"
    ).to_pandas()

    avg_daily = daily_data["VISITS"].mean()
    max_daily = daily_data["VISITS"].max()
    growth_rate = 0.0
    if len(daily_data) > 7:
        recent_avg = daily_data["VISITS"].tail(7).mean()
        past_avg = daily_data["VISITS"].head(7).mean()
        if past_avg > 0:
            growth_rate = ((recent_avg - past_avg) / past_avg) * 100

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">📈</div>
            <div class="kpi-value">{avg_daily:.0f}</div>
            <div class="kpi-label">Avg Daily Visits</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-orange">
            <div class="kpi-icon">🔝</div>
            <div class="kpi-value">{max_daily}</div>
            <div class="kpi-label">Peak Day Visits</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-green">
            <div class="kpi-icon">📊</div>
            <div class="kpi-value">{growth_rate:+.1f}%</div>
            <div class="kpi-label">Growth Trend</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        predicted_next_week = int(avg_daily * 7 * (1 + growth_rate / 100))
        st.markdown(f"""
        <div class="kpi-card kpi-card-purple">
            <div class="kpi-icon">🔮</div>
            <div class="kpi-value">{predicted_next_week}</div>
            <div class="kpi-label">Predicted Next Week</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("📉 Demand Forecast — Next 30 Days")
        if len(daily_data) > 0:
            last_date = daily_data["APPT_DATE"].max()
            future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=30)
            base = avg_daily
            daily_growth = growth_rate / 100 / 7
            forecast_values = [base * (1 + daily_growth * i) + (base * 0.1 * ((-1) ** i)) for i in range(30)]
            forecast_df = pd.DataFrame({"DATE": future_dates, "PREDICTED_VISITS": [int(v) for v in forecast_values]})
            combined = pd.concat([
                daily_data.rename(columns={"APPT_DATE": "DATE", "VISITS": "COUNT"}).assign(TYPE="Actual"),
                forecast_df.rename(columns={"PREDICTED_VISITS": "COUNT"}).assign(TYPE="Forecast")
            ])
            st.line_chart(combined, x="DATE", y="COUNT", color="TYPE")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("⚠️ No-Show Risk by Department")
            st.markdown("*Departments with highest no-show rates need intervention*")
            st.bar_chart(noshow_rate, x="DEPARTMENT", y="NOSHOW_RATE")
            high_risk = noshow_rate[noshow_rate["NOSHOW_RATE"] > noshow_rate["NOSHOW_RATE"].median()]
            if len(high_risk) > 0:
                st.warning(f"High-risk departments: {', '.join(high_risk['DEPARTMENT'].tolist())}")

    with col2:
        with st.container(border=True):
            st.subheader("🏥 Department Load Prediction")
            dept_load = session.sql(
                "SELECT DEPARTMENT, COUNT(*) AS TOTAL, ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT APPT_DATE), 1) AS DAILY_AVG FROM FACT_APPOINTMENTS GROUP BY DEPARTMENT ORDER BY DAILY_AVG DESC"
            ).to_pandas()
            dept_load["CAPACITY_STATUS"] = dept_load["DAILY_AVG"].apply(
                lambda x: "🔴 Overloaded" if x > dept_load["DAILY_AVG"].quantile(0.75)
                else ("🟡 Moderate" if x > dept_load["DAILY_AVG"].quantile(0.25) else "🟢 Normal")
            )
            st.dataframe(dept_load[["DEPARTMENT", "DAILY_AVG", "CAPACITY_STATUS"]], use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.subheader("💰 Revenue Forecast")
        rev_data = session.sql(
            "SELECT BILL_DATE, SUM(NET_AMOUNT) AS DAILY_REV FROM FACT_BILLING GROUP BY BILL_DATE ORDER BY BILL_DATE"
        ).to_pandas()
        if len(rev_data) > 0:
            rev_data["BILL_DATE"] = pd.to_datetime(rev_data["BILL_DATE"])
            avg_rev = rev_data["DAILY_REV"].mean()
            last_rev_date = rev_data["BILL_DATE"].max()
            future_rev_dates = pd.date_range(start=last_rev_date + pd.Timedelta(days=1), periods=30)
            rev_forecast = [float(avg_rev) * (1 + 0.02 * i / 30) for i in range(30)]
            rev_forecast_df = pd.DataFrame({"DATE": future_rev_dates, "REVENUE": rev_forecast})
            rev_combined = pd.concat([
                rev_data.rename(columns={"BILL_DATE": "DATE", "DAILY_REV": "REVENUE"}).assign(TYPE="Actual"),
                rev_forecast_df.assign(TYPE="Forecast")
            ])
            st.line_chart(rev_combined, x="DATE", y="REVENUE", color="TYPE")

            monthly_predicted = avg_rev * 30 * 1.02
            st.info(f"Predicted monthly revenue: ₹{monthly_predicted:,.0f} (based on current trend)")

    with st.container(border=True):
        st.subheader("🎯 Actionable Insights")
        peak_day = daily_data.loc[daily_data["VISITS"].idxmax()]
        slowest_day = daily_data.loc[daily_data["VISITS"].idxmin()]
        top_noshow = noshow_rate.iloc[0] if len(noshow_rate) > 0 else None

        insights = []
        insights.append(f"📌 **Peak demand day:** {peak_day['APPT_DATE'].strftime('%A, %b %d')} with {int(peak_day['VISITS'])} visits — ensure extra staff")
        insights.append(f"📌 **Lowest traffic day:** {slowest_day['APPT_DATE'].strftime('%A, %b %d')} with {int(slowest_day['VISITS'])} visits — optimize scheduling")
        if top_noshow is not None:
            insights.append(f"📌 **Highest no-show rate:** {top_noshow['DEPARTMENT']} at {top_noshow['NOSHOW_RATE']}% — consider reminder SMS/calls")
        if growth_rate > 0:
            insights.append(f"📌 **Growing demand:** {growth_rate:.1f}% weekly growth — plan capacity expansion")
        else:
            insights.append(f"📌 **Declining visits:** {growth_rate:.1f}% change — investigate patient drop-off")

        for insight in insights:
            st.markdown(insight)
