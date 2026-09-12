import os
import time
import streamlit as st
import pypdf
import google.genai as genai
import streamlit_mermaid as st_mermaid
from fpdf import FPDF


st.set_page_config(page_title="Noesis | AI Study Partner", layout="wide", initial_sidebar_state="expanded")


st.markdown("""
    <style>
    /* Hide top Streamlit header, footer, and GitHub icons */
    #GithubIcon {visibility: hidden;}
    header[data-testid="stHeader"] {visibility: hidden;}
    footer {visibility: hidden;}

    /* Deep Dark Purple to Black Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #0d0614 0%, #150a21 40%, #0a0410 100%);
        color: #f3e8ff;
    }

    /* Sidebar Background & Base Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d0716 !important;
        border-right: 1px solid #28153d;
    }

    /* FIX: Brighten Sidebar Text, Labels, and Radio Button Items */
    section[data-testid="stSidebar"] *, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #f3e8ff !important;
        font-weight: 500 !important;
    }

    /* Highlight Active Selected Navigation Item */
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        font-size: 1.05rem !important;
    }

    /* FIX: Make "Noesis" Title Larger & Soft Light Purple */
    section[data-testid="stSidebar"] h1 {
        color: #d8b4fe !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px;
    }

    /* Customizing Input & Uploader Containers */
    div[data-testid="stFileUploader"] {
        background-color: #160c26;
        border: 1px dashed #5c2d91;
        border-radius: 10px;
        padding: 10px;
    }

    /* Buttons Styling */
    .stButton > button {
        background: linear-gradient(90deg, #6b21a8 0%, #4c1d95 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #7e22ce 0%, #581c87 100%);
        box-shadow: 0px 0px 12px #7e22ce;
        color: white;
    }

    /* Expander Containers for History */
    div[data-testid="stExpander"] {
        background-color: #130a20;
        border: 1px solid #2c1547;
        border-radius: 8px;
    }

    /* Expand Mermaid SVG container */
    iframe[title="streamlit_mermaid.streamlit_mermaid"] {
        width: 100% !important;
        min-height: 550px !important;
    }
    svg[id^="mermaid-"] {
        max-width: 100% !important;
        width: 100% !important;
        height: auto !important;
    }
    </style>
""", unsafe_allow_html=True)


if "history" not in st.session_state:
    st.session_state.history = []


def create_pdf(text_content, title="Noesis Study Material"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    # Title
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(5)
    
    # Body text
    pdf.set_font("Helvetica", size=11)
    # Sanitize utf-8 characters for standard PDF output
    clean_text = text_content.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, 6, clean_text)
    
    return bytes(pdf.output())


api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")


st.sidebar.title("🔮 Noesis")
st.sidebar.caption("Your AI Learning Ecosystem")

nav_choice = st.sidebar.radio(
    "Navigation",
    [
        "📝 Revision Summary",
        "🗺️ Mind Map & Pictures",
        "❓ Quiz & Questions",
        "🛠️ Question Solver",
        "📜 History"
    ]
)


st.markdown("# Hey there")
st.markdown("### What's on your mind today?")
st.divider()


def extract_pdf_text(uploaded_file):
    reader = pypdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text[:15000]


def call_gemini(prompt):
    client = genai.Client(api_key=api_key)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            return response.text
        except Exception as err:
            if ("503" in str(err) or "UNAVAILABLE" in str(err)) and attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            st.error(f"Error communicating with AI service: {err}")
            return None


if nav_choice == "📝 Revision Summary":
    st.subheader("Generate Revision Summary & Key Points")
    uploaded_file = st.file_uploader("Upload Notes (PDF)", type=["pdf"], key="summary_pdf")
    
    if uploaded_file and api_key:
        if st.button("Generate Summary"):
            with st.spinner("Analyzing document with Noesis..."):
                text = extract_pdf_text(uploaded_file)
                prompt = (
                    "You are an expert high school tutor.\n"
                    "Provide a structured revision summary of the following notes:\n"
                    "- Key Concepts & Definitions\n"
                    "- High-Yield Bullet Points\n"
                    "- 3-5 Revision Flashcards (Q&A format)\n\n"
                    f"Notes:\n{text}"
                )
                output = call_gemini(prompt)
                
                if output:
                    st.markdown(output)
                    
                    st.session_state.history.append({"type": "Revision Summary", "content": output})
                    
                    pdf_bytes = create_pdf(output, title="Noesis - Revision Summary")
                    st.download_button(
                        label="📥 Download Summary as PDF",
                        data=pdf_bytes,
                        file_name="noesis_revision_summary.pdf",
                        mime="application/pdf"
                    )


elif nav_choice == "🗺️ Mind Map & Pictures":
    st.subheader("Generate Concept Mind Map & Visual Guidance")
    uploaded_file = st.file_uploader("Upload Notes (PDF)", type=["pdf"], key="mindmap_pdf")
    
    if uploaded_file and api_key:
        if st.button("Generate Diagram"):
            with st.spinner("Constructing visual mind map..."):
                text = extract_pdf_text(uploaded_file)
                prompt = (
                    "Provide two sections separated strictly by '---MINDMAP---':\n\n"
                    "SECTION 1: A short visual explanation of the main topic.\n\n"
                    "SECTION 2: A valid Mermaid.js flowchart (graph LR) mapping out concepts.\n"
                    "Rule: Do NOT use parentheses, quotes, or brackets inside node text.\n"
                    "Output ONLY valid mermaid code starting directly with 'graph LR' in Section 2.\n\n"
                    f"Notes:\n{text}"
                )
                output = call_gemini(prompt)
                
                if output:
                    parts = output.split("---MINDMAP---")
                    st.markdown(parts[0])
                    if len(parts) > 1:
                        diagram_code = parts[1].strip().replace("```mermaid", "").replace("```", "")
                        st.markdown("### 💡 Visual Mind Map")
                        try:
                            st_mermaid.st_mermaid(diagram_code, height=600)
                        except Exception:
                            st.code(diagram_code, language="mermaid")
                    
                    st.session_state.history.append({"type": "Mind Map Explanation", "content": parts[0]})


elif nav_choice == "❓ Quiz & Questions":
    st.subheader("Board Question Bank & Practice Quiz")
    uploaded_file = st.file_uploader("Upload Notes (PDF)", type=["pdf"], key="quiz_pdf")
    
    if uploaded_file and api_key:
        if st.button("Generate Quiz"):
            with st.spinner("Building assessment..."):
                text = extract_pdf_text(uploaded_file)
                prompt = (
                    "Act as a board examination creator. Create a practice assessment based on these notes:\n"
                    "1. 5 Multiple Choice Questions with answers.\n"
                    "2. 3 Short Answer Questions with model solutions.\n"
                    "3. 2 Analytical/Long Board-style Questions with detailed marking guidelines.\n\n"
                    f"Notes:\n{text}"
                )
                output = call_gemini(prompt)
                
                if output:
                    st.markdown(output)
                    
                    st.session_state.history.append({"type": "Quiz & Question Bank", "content": output})
                    
                    pdf_bytes = create_pdf(output, title="Noesis - Practice Quiz & Question Bank")
                    st.download_button(
                        label="📥 Download Quiz as PDF",
                        data=pdf_bytes,
                        file_name="noesis_practice_quiz.pdf",
                        mime="application/pdf"
                    )


elif nav_choice == "🛠️ Question Solver":
    st.subheader("Worksheet & Question Solver")
    uploaded_file = st.file_uploader("Upload Worksheet/Assignment (PDF)", type=["pdf"], key="solver_pdf")
    
    if uploaded_file and api_key:
        if st.button("Solve Questions"):
            with st.spinner("Solving questions step-by-step..."):
                text = extract_pdf_text(uploaded_file)
                prompt = (
                    "Act as an expert academic tutor.\n"
                    "1. Extract each question from the text.\n"
                    "2. Provide clear, step-by-step solutions with detailed reasoning.\n"
                    "3. Highlight formulas or key rules used.\n\n"
                    f"Text:\n{text}"
                )
                output = call_gemini(prompt)
                
                if output:
                    st.markdown(output)
                    
                    st.session_state.history.append({"type": "Worksheet Solutions", "content": output})
                    
                    pdf_bytes = create_pdf(output, title="Noesis - Worksheet Solutions")
                    st.download_button(
                        label="📥 Download Solutions as PDF",
                        data=pdf_bytes,
                        file_name="noesis_worksheet_solutions.pdf",
                        mime="application/pdf"
                    )


elif nav_choice == "📜 History":
    st.subheader("Session History & Saved Downloads")
    
    if not st.session_state.history:
        st.info("No saved study sessions yet! Use the sidebar navigation to generate summaries, quizzes, or solutions.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['type']} #{len(st.session_state.history) - idx}"):
                st.markdown(item["content"])
                
                pdf_bytes = create_pdf(item["content"], title=f"Noesis - {item['type']}")
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"noesis_{item['type'].lower().replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"hist_pdf_{idx}"
                )
