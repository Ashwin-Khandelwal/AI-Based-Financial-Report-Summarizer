# lightning_fast_app.py
import streamlit as st
import pandas as pd
from groq import Groq
from io import StringIO
import pdfplumber

st.set_page_config(page_title="Lightning Fast Analyzer", layout="wide")

# ---- MINIMAL SETUP ----
st.sidebar.header("🔑 API Key")
api_key = st.sidebar.text_input("Groq API Key", type="password")

if not api_key:
    st.warning("Enter API key to continue")
    st.stop()

client = Groq(api_key=api_key)

# ---- ULTRA-FAST FUNCTIONS ----
@st.cache_data
def extract_first_pages(pdf_file):
    """Extract only first 3-5 pages for speed"""
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            # Only first 3 pages - financial summary is usually here
            for i, page in enumerate(pdf.pages[:3]):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                # Stop at 10k characters max
                if len(text) > 10000:
                    break
        return text[:8000]  # Hard cutoff
    except:
        return ""

def quick_analyze(text, prompt):
    """Minimal API call"""
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",  # Fastest model
            messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}],
            temperature=0,
            max_tokens=300,  # Very short responses
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ---- STREAMLIT UI ----
st.title("⚡ Lightning Fast Financial Analyzer")
st.write("Super fast analysis - first 3 pages only")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    # Extract immediately on upload
    text = extract_first_pages(uploaded_file)
    
    if not text:
        st.error("Cannot read PDF")
        st.stop()
    
    st.success(f"✅ Ready! ({len(text)} characters)")
    
    # Show buttons immediately
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Summary"):
            result = quick_analyze(text, "Summarize key financial highlights in 100 words:")
            st.write(result)
    
    with col2:
        if st.button("📊 Numbers"):
            result = quick_analyze(text, "List main financial numbers (revenue, profit, etc):")
            st.write(result)
    
    with col3:
        if st.button("⚠️ Risks"):
            result = quick_analyze(text, "What are 3 main risks mentioned?")
            st.write(result)

# Performance note
st.markdown("---")
st.info("🚀 **Ultra-fast mode**: Analyzes first 3 pages only (~2-3 second response time)")