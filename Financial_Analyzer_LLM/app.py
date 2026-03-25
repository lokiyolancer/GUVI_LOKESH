import streamlit as st
import pdfplumber
import pandas as pd
import re
import requests
import matplotlib.pyplot as plt


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Financial Advisor", layout="wide")
st.title("💰 AI Financial Advisor")
st.caption("Upload your credit card statement PDF to analyze spending and generate AI advice.")


# ---------------- FUNCTIONS ----------------
def extract_pdf_lines(uploaded_file):
    lines = []
    with pdfplumber.open(uploaded_file) as pdf:
        total_pages = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.split("\n"))
    return lines, total_pages


def extract_transactions(lines):
    pattern = r"\d{2}-[A-Z]{3}-\d{2}"
    transactions = []
    for line in lines:
        if re.match(pattern, line):
            transactions.append(line)
    return transactions


def clean_transactions_func(transactions):
    ignore_words = [
        "IGST",
        "Fuel Trxn",
        "Interest",
        "PAYMENT RECEIVED"
    ]

    clean_transactions = []

    for row in transactions:
        if not any(word in row for word in ignore_words):
            clean_transactions.append(row)

    return clean_transactions


def create_dataframe(clean_transactions):
    data = []

    for row in clean_transactions:
        parts = row.split()
        date = parts[0]
        amount = parts[-1]
        description = " ".join(parts[2:-2])
        data.append([date, description, amount])

    df = pd.DataFrame(data, columns=["date", "description", "amount"])

    df["amount"] = df["amount"].str.replace(",", "", regex=False)
    df["amount"] = df["amount"].astype(float)
    df["date"] = pd.to_datetime(df["date"], format="%d-%b-%y")
    df["month"] = df["date"].dt.to_period("M").astype(str)

    return df


def categorize(text):
    text = text.lower()

    if "amazon" in text or "flipkart" in text:
        return "Online Shopping"

    if "fuel" in text or "bpcl" in text or "iocl" in text or "agencies" in text or "agenci" in text or "agency" in text:
        return "Fuel"

    if "irctc" in text:
        return "Travel"

    if "guvi" in text or "study" in text:
        return "Education"

    if "restaurant" in text or "hotel" in text or "kfc" in text or "rice" in text or "cake" in text:
        return "Food"

    if "bazaar" in text or "supermart" in text or "house" in text or "saravana" in text:
        return "Groceries"

    if "textile" in text or "tex" in text or "texti" in text or "jai sri krishnar" in text or "readymades" in text:
        return "Textiles"

    if "jewellery" in text:
        return "Jewellery"

    if "jio" in text:
        return "Bills"

    return "Other"


from groq import Groq
import os

# 🔑 TEMP: Put your API key directly (change later to env/secrets)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def ask_llm(prompt):
    try:
        # Initialize client
        client = Groq(api_key=GROQ_API_KEY)

        # Create completion
        response = client.chat.completions.create(
           model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a smart financial advisor. Analyze spending and give clear, practical advice."
                },
                {
                    "role": "user",
                    "content": f"""
User spending data:
{prompt}

Give:
- Key insights
- Wasteful spending
- Savings suggestions
- Budget advice
- Top 3 insights
-Exact money-saving tips
-Suggested monthly budget

Keep it simple and structured.
"""
                }
            ],
            temperature=0.7,
            max_completion_tokens=1024,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"LLM Error: {str(e)}"


# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Upload statement PDF", type=["pdf"])

if uploaded_file is not None:
    lines, total_pages = extract_pdf_lines(uploaded_file)
    transactions = extract_transactions(lines)
    clean_transactions = clean_transactions_func(transactions)
    df = create_dataframe(clean_transactions)

    df["category"] = df["description"].apply(categorize)

    monthly_spending = df.groupby("month")["amount"].sum()
    spending = df[df["amount"] > 0]["amount"].sum()
    
    top_merchants = df.groupby("description")["amount"].sum().sort_values(ascending=False)
    category_spending = df.groupby("category")["amount"].sum().sort_values(ascending=False)

    other_merchants = df[df["category"] == "Other"]["description"].unique()

    # ---------------- SUMMARY METRICS ----------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pages", total_pages)
    c2.metric("Transactions Found", len(transactions))
    c3.metric("Clean Transactions", len(clean_transactions))
    c4.metric("Net Amount Sum", f"₹{df['amount'].sum():,.2f}")

    c5, c6 = st.columns(2)
    c5.metric("Total Spending", f"₹{spending:,.2f}")
    
    # ---------------- DATA PREVIEW ----------------
    with st.expander("Preview cleaned data"):
        st.dataframe(df, use_container_width=True)

    # ---------------- CHARTS ----------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Spending")
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        monthly_spending.plot(kind="bar", ax=ax1)
        ax1.set_title("Monthly Spending")
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Amount (₹)")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

    with col2:
        st.subheader("Category Spending")
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        category_spending.plot(kind="bar", ax=ax2)
        ax2.set_title("Category Spending")
        ax2.set_xlabel("Category")
        ax2.set_ylabel("Amount (₹)")
        plt.xticks(rotation=45)
        st.pyplot(fig2)

    # ---------------- TOP MERCHANTS ----------------
    st.subheader("Top 10 Merchants")
    st.dataframe(top_merchants.head(10).reset_index().rename(columns={"index": "description", "amount": "total_amount"}), use_container_width=True)

    # ---------------- OTHER MERCHANTS ----------------
    st.subheader("Merchants categorized as Other")
    if len(other_merchants) > 0:
        st.write(list(other_merchants))
    else:
        st.success("No uncategorized merchants found.")

    # ---------------- AI ADVICE ----------------
    st.subheader("AI Financial Advice")

    summary = category_spending.to_string()

    prompt = f"""
You are a financial advisor.

Here is user spending:

{summary}

Give insights and saving suggestions.
"""

    if st.button("Generate AI Advice"):
        with st.spinner("Generating advice from local LLM..."):
            advice = ask_llm(prompt)
        st.markdown(advice)
