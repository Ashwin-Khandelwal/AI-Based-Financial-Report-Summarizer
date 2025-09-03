# app.py
import streamlit as st
import pdfplumber
import pandas as pd
from groq import Groq
from io import StringIO

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
    """Extract text from uploaded PDF and cache it"""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
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
            model="llama3-70b-8192",
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
        "summary": "Summarize the financial report in 200 words highlighting key performance trends.",
        "metrics": "Extract key financial metrics (Revenue, EBITDA, Net Profit, EPS, Debt) in tabular format from this report. Respond in CSV format.",
        "risks": "Identify top 5 risks and challenges discussed in this report in bullet points."
    }

    results = []
    progress = st.progress(0, text="Starting...")
    total = len(chunks)

    for i, chunk in enumerate(chunks, start=1):
        results.append(llm_call(f"{prompts[mode]}\n\n{chunk}"))
        progress.progress(i/total, text=f"Processing chunk {i}/{total}...")
    progress.empty()

    # --- Summary of summaries step ---
    combined = "\n".join(results)
    final_prompt = f"Combine and refine the following outputs into one coherent, concise result:\n\n{combined}"
    return llm_call(final_prompt)

# ---- STREAMLIT APP ----
st.title("📊 AI-Based Financial Report Summarizer (Groq)")
st.write("Upload an annual/quarterly financial report PDF to generate key insights.")

uploaded_file = st.file_uploader("Upload Financial Report (PDF)", type="pdf")

if uploaded_file is not None:
    with st.spinner("Extracting text..."):
        report_text = extract_text_from_pdf(uploaded_file)

    st.success("Report uploaded successfully ✅")

    # Tabs for different outputs
    tab1, tab2, tab3 = st.tabs(["📋 Executive Summary", "📈 Key Metrics", "⚠ Risks & Opportunities"])

    with tab1:
        if st.button("Generate Executive Summary"):
            chunks = list(chunk_text(safe_text(report_text)))
            summary = process_with_progress(chunks, mode="summary")
            st.write(summary)

    with tab2:
        if st.button("Extract Key Metrics"):
            chunks = list(chunk_text(safe_text(report_text)))
            metrics_output = process_with_progress(chunks, mode="metrics")

            # Try to parse CSV-like output into a table
            try:
                df = pd.read_csv(StringIO(metrics_output))
                st.table(df)
            except Exception:
                st.markdown(metrics_output)  # fallback: show raw text

    with tab3:
        if st.button("Identify Risks & Opportunities"):
            chunks = list(chunk_text(safe_text(report_text)))
            risks = process_with_progress(chunks, mode="risks")
            st.write(risks)
