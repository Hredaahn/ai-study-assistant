import streamlit as st
from google import genai
import pypdf
import streamlit_mermaid as st_mermaid

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="wide")
# Custom CSS to force Mermaid diagrams and text to render at full, legible scale
st.markdown("""
    <style>
    /* Expand the container for Mermaid iframe and SVG elements */
    iframe[title="streamlit_mermaid.streamlit_mermaid"] {
        width: 100% !important;
        min-height: 500px !important;
    }
    svg[id^="mermaid-"] {
        max-width: 100% !important;
        width: 100% !important;
        height: auto !important;
    }
    </style>
""", unsafe_allow_html=True)
st.title("📚 AI Student Study Assistant")
st.write("Upload your notes, and let AI condense them into revision guides & mind maps!")

# --- YOUR API KEY ---
api_key = "" 

# --- FILE UPLOADER BOX ---
uploaded_file = st.file_uploader("Upload your study notes (PDF or TXT)", type=["pdf", "txt"])

if uploaded_file:
    extracted_text = ""
    
    # Read TXT file
    if uploaded_file.name.endswith(".txt"):
        extracted_text = uploaded_file.read().decode("utf-8")
        
    # Read PDF file
    elif uploaded_file.name.endswith(".pdf"):
        pdf_reader = pypdf.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

    st.success(f"File uploaded! Read {len(extracted_text)} characters.")
    
    # Action Button
    if st.button("✨ Generate Revision Guide & Mind Map"):
        truncated_text = extracted_text[:8000]

        try:
            with st.spinner("Analyzing notes & constructing detailed mind map..."):
                client = genai.Client(api_key=api_key)
                
                prompt = (
                    "You are an expert high school study assistant.\n"
                    "Provide two sections in your response separated by '---MINDMAP---':\n\n"
                    "SECTION 1: A concise revision summary with bullet points, bold key terms, and 3 flashcards.\n\n"
                    "SECTION 2: A detailed Mermaid.js flowchart (graph LR) that maps out actual, specific concepts from the text.\n"
                    "Rule: Do NOT use brackets, parentheses, or quotes inside node labels (e.g. A[Photosynthesis] --> B[Light Reactions]).\n"
                    "Output ONLY the mermaid code in section 2 starting directly with 'graph LR'.\n\n"
                    f"Notes:\n{truncated_text}"
                )
                
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
                
                raw_response = response.text
                
                # Split summary and mindmap reliably
                if "---MINDMAP---" in raw_response:
                    summary_part, diagram_part = raw_response.split("---MINDMAP---", 1)
                else:
                    summary_part = raw_response
                    diagram_part = ""

                # Clean up diagram string
                diagram_code = diagram_part.strip().strip("`").replace("mermaid", "").strip()

                # Display Text Summary
                st.markdown("### 📝 Revision Summary & Flashcards")
                st.write(summary_part.strip())
                
                # Display Mind Map
                if diagram_code:
                    st.markdown("### 💡 Concept Mind Map")
                    try:
                        st_mermaid.st_mermaid(diagram_code, height=800)
                    except Exception:
                        st.code(diagram_code, language="mermaid")

        except Exception as e:
            st.error(f"An error occurred: {e}")