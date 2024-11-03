import streamlit as st
import pandas as pd
import PyPDF2  # PDF processing
import requests 
import json
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Access the API key
api_key = os.getenv("OPENAI_API_KEY")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# extract data from PDF
def extract_pdf_data(file):
    reader = PyPDF2.PdfReader(file)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

# process PDF data into a JSON format
def process_pdf_data(text):
    transactions = []

    lines = text.split("\n")
    for line in lines:
        parts = line.split()  
        if len(parts) >= 3: 
            transaction = {
                "date": parts[0],  
                "description": " ".join(parts[1:-1]), 
                "amount": float(parts[-1]) 
            }
            transactions.append(transaction)
    return json.dumps(transactions)

# handle CSV upload and convert to JSON
def handle_csv(file):
    df = pd.read_csv(file)
    return df.to_json(orient="records")  # Convert DataFrame to JSON

# get financial advice from OpenAI API
def get_financial_advice(data):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": f"scrape the bank statement and output: total income, total spending, and give the top 3 categories that contributed towards spending. DONT SHOW YOUR WORKING JUST GIVE THE RESULT ...start by saying 'from the provided statements, here are the results..ALWAYS SAY THIS. THEN BEFORE outputting the top 3 categories, say here are the top 5 categories ALWAYS SAY THIS. now..review the top 5 categories and give a score out of 100 on the carbon footprint that the top 5 categories contribute to. explain how each category contributes towards the footprint and the score it contributes towards the total. before you say that say 'here is your estimated carbon footprint score' then at the bottom give a 'Tips that will contribute towards less carbon footprint' : {data}"}],
        "temperature": 0.2,
        "max_tokens": 700
    }
    
    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        advice = response.json()
        return advice['choices'][0]['message']['content'] 
    else:
        return "Error getting advice: {}".format(response.status_code)
    

# render the Streamlit app
def main():
    st.title("Better Decisions.Ai")

    st.write("BetterDecisions Ai helps you identify key areas in your spending that habits that contribute the most to your carbon footprint.")

    uploaded_file = st.file_uploader("Upload your bank statement to get tips on how to reduce your carbon footprint", type=["pdf", "csv"])

    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            data = extract_pdf_data(uploaded_file)
            structured_data = process_pdf_data(data) 
        elif uploaded_file.type == "text/csv":
            structured_data = handle_csv(uploaded_file) 

        # get financial advice based on the uploaded data
        if st.button("Get Tips"):
            with st.spinner("Please wait a few moments..."):
                advice = get_financial_advice(structured_data)
            st.write(advice)

if __name__ == "__main__":
    load_css("styles.css")
    main()
