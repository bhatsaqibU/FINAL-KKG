# FINAL VERSION - KISAN KHIDMAT GHAR APP
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from reportlab.pdfgen import canvas
import requests

st.set_page_config(page_title="Kisan Khidmat Ghar", layout="centered")

# Constants
ADMIN_PASSWORD = "Saqib@0987fayaz"
DATA_FOLDER = "customer_data"
IMAGE_FOLDER = "consultation_images"
LOG_FILE = "message_log.csv"
WEATHER_API_KEY = "2bd3f3cd2891616187a97d833de7e570"
LOCATION = "Chakoora,IN"

# Ensure folders exist
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Helper functions
def load_customer_file(phone):
    file_path = os.path.join(DATA_FOLDER, f"{phone}.csv")
    return pd.read_csv(file_path) if os.path.exists(file_path) else pd.DataFrame(columns=["Date", "Item", "Amount", "Paid"])

def save_customer_file(phone, df):
    file_path = os.path.join(DATA_FOLDER, f"{phone}.csv")
    df.to_csv(file_path, index=False)

def generate_pdf(phone, df):
    filename = f"{phone}_bill.pdf"
    c = canvas.Canvas(filename)
    c.drawString(100, 800, f"Kisan Khidmat Ghar - Bill for {phone}")
    y = 770
    for i, row in df.iterrows():
        c.drawString(100, y, f"{row['Date']} | {row['Item']} | ₹{row['Amount']} | Paid: ₹{row['Paid']}")
        y -= 20
    c.save()
    return filename

def get_total_dues(df):
    return df["Amount"].sum() - df["Paid"].sum()

def log_message(phone, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_df = pd.DataFrame([[phone, message, now]], columns=["Phone", "Message", "Date"])
    if os.path.exists(LOG_FILE):
        existing = pd.read_csv(LOG_FILE)
        log_df = pd.concat([existing, log_df], ignore_index=True)
    log_df.to_csv(LOG_FILE, index=False)

def get_weather_recommendation():
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()
        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        if "rain" in desc:
            return f"🌧️ It’s raining today. Avoid spraying. ({desc}, {temp}°C)"
        elif temp > 30:
            return f"☀️ It's too hot. Spray in evening. ({desc}, {temp}°C)"
        else:
            return f"✅ Good weather for spraying. ({desc}, {temp}°C)"
    except:
        return "⚠️ Weather info not available."

# UI START
st.markdown("<h1 style='text-align: center;'>🌾 Kisan Khidmat Ghar</h1>", unsafe_allow_html=True)

menu = st.sidebar.radio("Login Type", ["Customer Login", "Admin Login", "Register New Customer"])

if menu == "Register New Customer":
    st.subheader("📱 Register New Customer")
    name = st.text_input("Customer Name")
    phone = st.text_input("Phone Number")
    if st.button("Register"):
        if name and phone:
            file_path = os.path.join(DATA_FOLDER, f"{phone}.csv")
            if os.path.exists(file_path):
                st.warning("Customer already exists!")
            else:
                pd.DataFrame(columns=["Date", "Item", "Amount", "Paid"]).to_csv(file_path, index=False)
                st.success("✅ Customer registered successfully!")
        else:
            st.error("Please enter name and phone number.")

elif menu == "Customer Login":
    phone = st.text_input("Enter your phone number")
    if st.button("Login"):
        df = load_customer_file(phone)
        if not df.empty:
            st.success("Login successful!")
            st.header("📄 Your Records")
            st.dataframe(df)
            st.markdown(f"### 💰 Unpaid Balance: ₹{get_total_dues(df)}")
            if st.button("Download PDF Bill"):
                file = generate_pdf(phone, df)
                with open(file, "rb") as f:
                    st.download_button("📥 Download PDF", f, file_name=file)
        else:
            st.error("Customer not found!")

elif menu == "Admin Login":
    password = st.text_input("Enter Admin Password", type="password")
    if password == ADMIN_PASSWORD:
        st.success("Admin access granted!")

        # View All Customers
        st.subheader("📊 Dashboard")
        all_files = os.listdir(DATA_FOLDER)
        total_dues = 0
        top_customers = []
        for file in all_files:
            df = pd.read_csv(os.path.join(DATA_FOLDER, file))
            due = get_total_dues(df)
            total_dues += due
            top_customers.append((file.replace(".csv", ""), due))
        st.markdown(f"### 💰 Total Outstanding Dues: ₹{total_dues}")
        top_customers.sort(key=lambda x: x[1], reverse=True)
        st.markdown("### ⭐ Top Customers:")
        for phone, due in top_customers[:5]:
            st.markdown(f"📞 {phone} - ₹{due}")

        # Manage Customer Records
        st.subheader("✏️ Edit Customer Records")
        phone = st.text_input("Phone to Edit")
        if phone:
            df = load_customer_file(phone)
            st.dataframe(df)
            with st.form("edit_form"):
                row_idx = st.number_input("Row Index to Edit", min_value=0, max_value=len(df)-1 if len(df) > 0 else 0)
                new_date = st.date_input("Edit Date", datetime.today())
                new_item = st.text_input("Edit Item", value=df.iloc[row_idx]["Item"] if len(df) > 0 else "")
                new_amount = st.number_input("Edit Amount", value=float(df.iloc[row_idx]["Amount"]) if len(df) > 0 else 0.0)
                new_paid = st.number_input("Edit Paid", value=float(df.iloc[row_idx]["Paid"]) if len(df) > 0 else 0.0)
                if st.form_submit_button("Submit Edit"):
                    df.at[row_idx, "Date"] = new_date
                    df.at[row_idx, "Item"] = new_item
                    df.at[row_idx, "Amount"] = new_amount
                    df.at[row_idx, "Paid"] = new_paid
                    save_customer_file(phone, df)
                    st.success("✅ Record updated.")

            if st.button("Delete Last Entry"):
                if not df.empty:
                    df = df[:-1]
                    save_customer_file(phone, df)
                    st.warning("Last record deleted.")

        # Add Entry
        st.subheader("➕ Add New Entry")
        with st.form("add_form"):
            phone = st.text_input("Customer Phone")
            date = st.date_input("Date", datetime.today())
            item = st.text_input("Item")
            amount = st.number_input("Amount", min_value=0.0)
            paid = st.number_input("Paid", min_value=0.0)
            if st.form_submit_button("Add Entry"):
                df = load_customer_file(phone)
                new_row = {"Date": date, "Item": item, "Amount": amount, "Paid": paid}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_customer_file(phone, df)
                st.success("✅ Entry added.")

        # WhatsApp Log
        st.subheader("📤 WhatsApp Message Log")
        with st.form("msg_form"):
            phone = st.text_input("Phone")
            msg = st.text_area("Message")
            if st.form_submit_button("Log Message"):
                log_message(phone, msg)
                st.success("Message logged!")

        if os.path.exists(LOG_FILE):
            st.markdown("### 🧾 Message History")
            st.dataframe(pd.read_csv(LOG_FILE))

        # Expert Consultation
        st.subheader("🧑‍🌾 Upload Image for Expert")
        phone = st.text_input("Phone (for Consultation Upload)")
        img = st.file_uploader("Upload Image")
        if img and phone:
            img_path = os.path.join(IMAGE_FOLDER, f"{phone}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
            with open(img_path, "wb") as f:
                f.write(img.read())
            st.success("✅ Image uploaded for expert consultation.")

        # Weather Suggestion
        st.subheader("🌦️ AI Spray Recommendation")
        st.info(get_weather_recommendation())

    else:
        st.warning("Enter correct admin password!")

# Footer
st.markdown("<hr><center>🚀 <b>Powered by Bhat Saqib</b></center>", unsafe_allow_html=True)
