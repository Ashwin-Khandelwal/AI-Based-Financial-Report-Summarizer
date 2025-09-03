# app.py
import streamlit as st
import pandas as pd
from groq import Groq
from io import StringIO

# Primary PDF parser
import pdfplumber
# Backup parser
from PyPDF2 import PdfReader

st.set_page_config(page_title="Financial Report Summarizer (Groq)", layout="wide")

# ---- INPUT: API KEY ----
st.sidebar.header("🔑 API Settings")
api_key = st.sidebar.text_input("Enter your Groq API Key", type="password")

if api_key:
    client = Groq(api_key=api_key)
else:
    st.warning("Please enter your Groq API key in the sidebar to continue.")
    st.stop()

# ---- FUNCTIONS ----
@st.cache_data
def extract_text_from_pdf(pdf_file):
    """Extract text using pdfplumber, fallback to PyPDF2 if needed"""
    text = ""

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        if text.strip():
            return text
    except Exception as e:
        st.warning(f"⚠️ pdfplumber failed, switching to backup parser. Error: {e}")

    # Backup: PyPDF2
    try:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        st.error(f"❌ Both PDF parsers failed. Error: {e}")
        return ""

    return text

def chunk_text(text, chunk_size=3000):
    """Split text into smaller chunks for LLM processing"""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i+chunk_size])

def safe_text(text, max_tokens=7000):
    """Truncate text if it exceeds token limit"""
    words = text.split()
    if len(words) > max_tokens:
        return " ".join(words[:max_tokens])
    return text

def llm_call(prompt):
    """Generic Groq API wrapper with error handling"""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a financial analyst assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error calling Groq API: {e}"

def process_with_progress(chunks, mode):
    """Process multiple chunks with progress bar and summary of summaries"""
    prompts = {
        "summary": "Summarize the financial

