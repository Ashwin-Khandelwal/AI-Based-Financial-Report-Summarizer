# fast_app.py
import streamlit as st
import pandas as pd
from groq import Groq
from io import StringIO
import pdfplumber
from PyPDF2 import PdfReader

st.set_page_config(page_title="Fast Financial Analyzer", layout="wide")

# ---- SIDEBAR ----
st.sidebar.header("🔑 Settings")
api_key = st.sidebar.text_input("Groq API Key", type="password")

if not api_key:
    st.warning("⚠️ Please enter your Groq API key to continue")
    st.stop()

client = Groq(api_key=api_key)

# ---- FAST FUNCTIONS ----
@st.cache_data
def extract_pdf_text(pdf_file):
    """Fast PDF extraction with smart truncation"""
    text = ""
    
    try:
        # Try pdfplumber first (better quality)
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages[:20]:  # Limit to first 20 pages for speed
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                if len(text) > 50000:  # Stop at ~50k chars
                    break
    except:
        # Fallback to PyPDF2
        try:
            reader = PdfReader(pdf_file)
            for i, page in enumerate(reader.pages[:15]):  # Even fewer pages for fallback
                text += page.extract_text() + "\n"
                if len(text) > 40000:
                    break
        except:
            return ""
    
    return text[:45000]  # Hard limit for API efficiency

def smart_truncate(text, max_chars=20000):
    """Keep important sections, truncate middle"""
    if len(text) <= max_chars:
        return text
    
    # Keep first 40% and last 40%, skip middle 20%
    start_len = int(max_chars * 0.4)
    end_len = int(max_chars * 0.4)
    
    start = text[:start_len]
    end = text[-end_len:]
    
    return f"{start}\n\n[... MIDDLE SECTION TRUNCATED ...]\n\n{end}"

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def analyze_report(_client, text, analysis_type):
    """Single API call for each analysis type"""
    
    prompts = {
        "summary": f"""Analyze this financial report and provide a concise executive summary in 150-200 words:

{text}

Focus on: Revenue trends, profitability, key developments, and outlook.""",

        "metrics": f"""Extract key financial metrics from this report and format as CSV:

{text}

Required format:
Metric,Current Period,Previous Period,Change
Revenue,[amount],[amount],[%]
Net Income,[amount],[amount],[%]
EBITDA,[amount],[amount],[%]
EPS,[amount],[amount],[%]
Total Assets,[amount],[amount],[%]
Total Debt,[amount],[amount],[%]

Use actual numbers from the report. Write 'N/A' if not found.""",

        "risks": f"""Identify the top 5 risks and opportunities from this financial report:

{text}

Format as:
RISKS:
• [Risk 1]
• [Risk 2]
• [Risk 3]

OPPORTUNITIES:
• [Opportunity 1]
• [Opportunity 2]"""
    }
    
    try:
        response = _client.chat.completions.create(
            model="openai/gpt-oss-20b",  # Fast, reliable model
            messages=[
                {"role": "system", "content": "You are a financial analyst. Provide accurate, concise analysis."},
                {"role": "user", "content": prompts[analysis_type]}
            ],
            temperature=0.1,
            max_tokens=800,  # Limit response length for speed
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---- STREAMLIT UI ----
st.title("⚡ Fast Financial Report Analyzer")
st.write("Upload a PDF financial report for instant analysis (optimized for speed)")

# File upload
uploaded_file = st.file_uploader("📁 Upload PDF Report", type="pdf")

if uploaded_file:
    # Show file info
    file_size = uploaded_file.size / (1024*1024)  # MB
    st.info(f"📄 File: {uploaded_file.name} ({file_size:.1f} MB)")
    
    # Extract text with progress
    with st.spinner("🔍 Extracting text..."):
        report_text = extract_pdf_text(uploaded_file)
    
    if not report_text.strip():
        st.error("❌ Could not extract text from PDF")
        st.stop()
    
    # Show extraction success
    word_count = len(report_text.split())
    st.success(f"✅ Extracted {word_count:,} words from report")
    
    # Smart truncation for API efficiency
    processed_text = smart_truncate(report_text)
    
    # ---- ANALYSIS BUTTONS (Side by side) ----
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Executive Summary", use_container_width=True):
            with st.spinner("Analyzing..."):
                summary = analyze_report(client, processed_text, "summary")
            st.subheader("Executive Summary")
            st.write(summary)
    
    with col2:
        if st.button("📊 Key Metrics", use_container_width=True):
            with st.spinner("Extracting metrics..."):
                metrics = analyze_report(client, processed_text, "metrics")
            st.subheader("Financial Metrics")
            
            # Try to display as table
            try:
                if "," in metrics and "\n" in metrics:
                    df = pd.read_csv(StringIO(metrics))
                    st.dataframe(df, use_container_width=True)
                else:
                    st.text(metrics)
            except:
                st.text(metrics)
    
    with col3:
        if st.button("⚠️ Risks & Opportunities", use_container_width=True):
            with st.spinner("Identifying risks..."):
                risks = analyze_report(client, processed_text, "risks")
            st.subheader("Risks & Opportunities")
            st.write(risks)
    
    # ---- QUICK STATS ----
    with st.expander("📈 Quick Stats", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words Extracted", f"{word_count:,}")
        with col2:
            st.metric("Pages Processed", "~20 max")
        with col3:
            st.metric("Processing Time", "~5-10 sec")

# ---- FOOTER ----
st.markdown("---")
st.markdown("💡 **Speed Optimizations**: Limited pages, smart text truncation, single API calls, caching enabled")