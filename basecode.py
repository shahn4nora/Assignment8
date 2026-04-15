import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="AI Operations Assistant", layout="wide")

st.title("AI Operations Assistant for Small Fitness Studios")
st.write(
    "Upload your attendance CSV to get AI-powered insights on attendance, churn risk, and retention actions."
)

uploaded_file = st.file_uploader("Upload attendance CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.subheader("Preview of Uploaded Data")
        st.dataframe(df.head())

        required_columns = [
            "member_id",
            "member_name",
            "last_check_in",
            "total_visits_last_30_days",
            "plan_type",
            "class_name",
            "class_datetime",
        ]
        missing = [c for c in required_columns if c not in df.columns]

        if missing:
            st.error(
                f"The following required columns are missing from your CSV: {', '.join(missing)}"
            )
        else:
            df["last_check_in"] = pd.to_datetime(df["last_check_in"])
            df["class_datetime"] = pd.to_datetime(df["class_datetime"])

            st.markdown("---")
            st.subheader("AI-Generated Insights")

            today = datetime.date(2024, 10, 8)
            tomorrow = today + datetime.timedelta(days=1)

            recent_classes = df[df["class_datetime"].dt.date >= today - datetime.timedelta(days=7)]
            avg_attendance = recent_classes.groupby(
                recent_classes["class_datetime"].dt.date
            )["member_id"].nunique().mean()

            st.markdown("### 📈 Attendance Prediction")
            st.write(
                f"**Estimated attendance for tomorrow ({tomorrow}):** "
                f"{int(round(avg_attendance)) if not pd.isna(avg_attendance) else 'Not enough data'} members"
            )

            st.markdown("### ⚠️ Members at Risk of Churn")
            churn_threshold_days = 10
            low_visits_threshold = 2

            df["days_since_last_check_in"] = (today - df["last_check_in"].dt.date).dt.days
            churn_risk = df[
                (df["days_since_last_check_in"] > churn_threshold_days)
                | (df["total_visits_last_30_days"] <= low_visits_threshold)
            ][
                [
                    "member_id",
                    "member_name",
                    "last_check_in",
                    "total_visits_last_30_days",
                    "plan_type",
                    "days_since_last_check_in",
                ]
            ]

            if churn_risk.empty:
                st.write("No clear churn-risk members based on current thresholds.")
            else:
                st.write("These members may be at risk of canceling:")
                st.dataframe(churn_risk)

            st.markdown("### 💡 Retention Recommendations")
            recommendations = []
            for _, row in churn_risk.iterrows():
                msg = (
                    f"- **{row['member_name']}** (ID {row['member_id']}): "
                    f"{row['days_since_last_check_in']} days since last check-in, "
                    f"{row['total_visits_last_30_days']} visits in last 30 days. "
                    f"Recommend sending a personalized reactivation message or offering a class reminder."
                )
                recommendations.append(msg)

            if recommendations:
                for r in recommendations:
                    st.write(r)
            else:
                st.write("No specific retention actions recommended at this time.")

            st.markdown("---")
            st.subheader("Ask a Question About Your Studio Data")

            user_question = st.text_input(
                "Type a question (e.g., 'Who hasn't checked in this week?')"
            )

            if user_question:
                st.markdown("### 🤖 AI Response")

                q = user_question.lower()

                if "hasn't checked in this week" in q or "has not checked in this week" in q:
                    start_of_week = today - datetime.timedelta(days=today.weekday())
                    checked_in_this_week = df[
                        df["last_check_in"].dt.date >= start_of_week
                    ]
                    not_checked_in = df[~df["member_id"].isin(checked_in_this_week["member_id"])][
                        ["member_id", "member_name", "last_check_in"]
                    ]
                    if not_checked_in.empty:
                        st.write("All active members have checked in at least once this week.")
                    else:
                        st.write("Members who have not checked in this week:")
                        st.dataframe(not_checked_in)

                elif "low attendance" in q or "low-utilization classes" in q:
                    class_counts = df.groupby("class_name")["member_id"].nunique().reset_index()
                    low_classes = class_counts[class_counts["member_id"] <= 2]
                    if low_classes.empty:
                        st.write("No classes with clearly low attendance based on this dataset.")
                    else:
                        st.write("Classes with relatively low attendance:")
                        st.dataframe(low_classes)

                else:
                    st.write(
                        "This prototype currently supports questions like:\n"
                        "- 'Who hasn't checked in this week?'\n"
                        "- 'Which classes have low attendance?'\n"
                        "For other questions, a full AI model would be used."
                    )

    except Exception as e:
        st.error(f"There was an error processing your file: {e}")
else:
    st.info("Please upload a CSV file to begin.")
