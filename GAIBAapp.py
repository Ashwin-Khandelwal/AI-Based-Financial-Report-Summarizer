# app.py
import streamlit as st
import pdfplumber
from groq import Groq

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
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def chunk_text(text, chunk_size=3000):
    """Split text into smaller chunks for LLM processing."""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i+chunk_size])

def llm_summarize(text, mode="summary"):
    """Call Groq LLM for different modes: summary, metrics, risks."""
    prompts = {
        "summary": "Summarize the financial report in 200 words highlighting key performance trends.",
        "metrics": "Extract key financial metrics (Revenue, EBITDA, Net Profit, EPS, Debt) in tabular format from this report.",
        "risks": "Identify top 5 risks and challenges discussed in this report in bullet points."
    }

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",  # you can also try "mixtral-8x7b-32768"
        messages=[
            {"role": "system", "content": "You are a financial analyst assistant."},
            {"role": "user", "content": f"{prompts[mode]}\n\n{text}"}
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content

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
            chunks = list(chunk_text(report_text))
            summary = ""
            for chunk in chunks:
                summary += llm_summarize(chunk, mode="summary") + "\n"
            st.write(summary)

    with tab2:
        if st.button("Extract Key Metrics"):
            chunks = list(chunk_text(report_text))
            metrics = ""
            for chunk in chunks:
                metrics += llm_summarize(chunk, mode="metrics") + "\n"
            st.markdown(metrics)

    with tab3:
        if st.button("Identify Risks & Opportunities"):
            chunks = list(chunk_text(report_text))
            risks = ""
            for chunk in chunks:
                risks += llm_summarize(chunk, mode="risks") + "\n"
            st.write(risks)