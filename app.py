import streamlit as st
import google.generativeai as genai
import PyPDF2
import docx
import io
import os
from dotenv import load_dotenv
import difflib
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm
from io import BytesIO
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="AI Document Comparator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for attractive interface
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(45deg, #FF1744, #E91E63, #9C27B0, #673AB7);
        background-size: 300% 300%;
        animation: headerGlow 4s ease-in-out infinite;
        padding: 4rem 2rem;
        border-radius: 25px;
        margin-bottom: 3rem;
        text-align: center;
        color: white;
        box-shadow: 
            0 0 40px rgba(255, 23, 68, 0.4),
            0 20px 60px rgba(156, 39, 176, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        border: 4px solid transparent;
        background-clip: padding-box;
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #FFD700, #FF69B4, #00BFFF, #32CD32);
        background-size: 400% 400%;
        animation: borderGlow 3s ease-in-out infinite;
        border-radius: 27px;
        z-index: -1;
    }
    
    @keyframes headerGlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes borderGlow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }  /* Fixed: Added missing closing brace */
    
    .main-header h1 {
        font-size: 3.2rem;
        font-weight: 900;
        margin: 0 0 0.8rem 0;
        text-shadow: 
            2px 2px 8px rgba(0,0,0,0.6),
            0 0 20px rgba(255, 255, 255, 0.3),
            0 0 40px rgba(255, 23, 68, 0.5);
        color: #FFFFFF;
        letter-spacing: 2px;
        text-transform: uppercase;
        animation: textPulse 2s ease-in-out infinite;
    }
    
    @keyframes textPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    .main-header p {
        font-size: 1.4rem;
        margin: 0;
        font-weight: 500;
        color: #FFF8E1;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.5);
        opacity: 0.95;
        letter-spacing: 1px;
    }
    
    .warning-box {
        background: #FFF8E1;
        color: #F57F17;
        padding: 2rem;
        border-radius: 12px;
        border: 3px solid #FFC107;
        margin: 1rem 0;
        box-shadow: 0 8px 20px rgba(255, 193, 7, 0.3);
    }
    
    .success-box {
        background: #E8F5E8;
        color: #2E7D32;
        padding: 2rem;
        border-radius: 12px;
        border: 3px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 8px 20px rgba(76, 175, 80, 0.3);
    }
    .stDataFrame {
        max-width: 800px; /* Reduce table width */
        overflow-x: auto;
    }
    .stDataFrame table {
        width: 100%;
        table-layout: fixed; /* Ensure columns respect width */
    }
    .stDataFrame th, .stDataFrame td {
        word-wrap: break-word; /* Wrap long text */
        max-width: 200px; /* Limit column width */
        overflow: hidden;
        text-overflow: ellipsis; /* Truncate long text with ellipsis */
    }
    
    .download-section {
        background: #F5F5F5;
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #ddd;
        margin: 2rem 0;
        display: block !important;
        visibility: visible !important;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #FF1744, #E91E63, #9C27B0, #673AB7);
        color: white !important;
        border-radius: 30px;
        border: 3px solid transparent;
        padding: 1rem 2.5rem;
        font-weight: 800;
        font-size: 1.1rem;
        transition: all 0.3s;
        box-shadow: 0 8px 25px rgba(255, 23, 68, 0.4);
        display: block !important;
        visibility: visible !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(255, 23, 68, 0.5);
        background: linear-gradient(45deg, #D81B60, #C2185B, #7B1FA2, #512DA8);
        border-color: #FF1744;
    }
    
    .stDownloadButton > button {
        background: linear-gradient(45deg, #2196F3, #03A9F4, #00BCD4, #009688);
        color: white !important;
        border-radius: 15px;
        border: 2px solid #2196F3;
        padding: 0.8rem 1.5rem;
        font-weight: 700;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
        margin: 0.5rem;
        display: inline-block !important;
        visibility: visible !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(33, 150, 243, 0.4);
        background: linear-gradient(45deg, #1976D2, #0288D1, #0097A7, #00796B);
    }
    
    .element-container {
        display: block !important;
        visibility: visible !important;
    }
    
    .stMarkdown {
        display: block !important;
        visibility: visible !important;
    }
    
    .stExpander {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .metric-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
    }
    
    .stFileUploader {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .stTextArea {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    .stApp .stWidget {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Gemini AI
@st.cache_resource
def initialize_ai():
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Gemini API key not found! Please add it to your .env file")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        return model
    except Exception as e:
        st.error(f"❌ Error initializing AI: {str(e)}")
        return None

# Extract text from PDF
def extract_pdf_text(file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return None

# Extract text from Word document
def extract_docx_text(file):
    try:
        doc = docx.Document(io.BytesIO(file.read()))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"❌ Error reading Word document: {str(e)}")
        return None

# Extract text from JSON document
def extract_json_text(file):
    try:
        data = json.load(io.BytesIO(file.read()))
        # Convert JSON to string, handling nested structures
        def flatten_json(obj, parent_key='', sep='.'):
            items = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    items.extend(flatten_json(v, new_key, sep).items())
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                    items.extend(flatten_json(v, new_key, sep).items())
            else:
                items.append((parent_key, str(obj)))
            return dict(items)
        
        flat_data = flatten_json(data)
        text = "\n".join([f"{key}: {value}" for key, value in flat_data.items()])
        return text.strip()
    except Exception as e:
        st.error(f"❌ Error reading JSON: {str(e)}")
        return None

# Extract text based on file type
def extract_text(file):
    if file.type == "application/pdf":
        return extract_pdf_text(file)
    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        return extract_docx_text(file)
    elif file.type == "text/plain":
        return str(file.read(), "utf-8")
    elif file.type == "application/json":
        return extract_json_text(file)
    else:
        st.error("❌ Unsupported file format! Please upload PDF, Word, TXT, or JSON files.")
        return None

# Compare documents using AI
def compare_documents_ai(original_text, revised_text, model):
    try:
        prompt = f"""
        You are an expert document analyst. Compare these two documents and provide a comprehensive analysis:

        ORIGINAL DOCUMENT:
        {original_text[:4000]}

        REVISED DOCUMENT:
        {revised_text[:4000]}

        Please provide a detailed analysis with the following sections:

        1. Executive Summary: Brief overview of what changed between the documents

        2. Key Changes Identified: 
           - List the most significant modifications
           - Highlight additions, deletions, and modifications
           - Note any structural changes

        3. Content Analysis:
           - Compare tone and style differences
           - Identify changes in terminology or language
           - Note any formatting or organizational changes

        4. Detailed Comparison:
           - Provide specific before/after examples of important changes
           - Quote relevant sections that were modified
           - Explain the context of each change

        5. Impact Assessment:
           - What do these changes mean?
           - How might they affect the document's purpose or audience?
           - Are there any potential implications or consequences?

        6. Change Categories:
           - Classify changes as: Minor edits, Substantial revisions, Critical updates
           - Identify patterns in the types of changes made

        7. Quality & Consistency:
           - Comment on the overall quality of changes
           - Note any inconsistencies or potential issues
           - Suggest areas that might need attention

        8. Recommendations:
           - Any suggestions for further improvements
           - Flag any concerns or potential problems
           - Highlight positive changes

        Format your response with clear headers, bullet points, and examples for easy reading.
        Be thorough but concise, focusing on the most meaningful differences.
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ Error in AI comparison: {str(e)}")
        return None

# Helper function to process Markdown for different formats
def process_markdown(text, output_format="txt"):
    """
    Process Markdown text to convert or remove formatting based on the output format.
    - For TXT: Remove Markdown symbols, keep plain text.
    - For PDF/DOCX: Parse headings, bold, italic, and lists for formatting.
    - For JSON: Keep raw Markdown but ensure proper structure.
    """
    lines = text.splitlines()
    processed_lines = []
    current_heading_level = 0

    for line in lines:
        line = line.strip()
        if not line:
            processed_lines.append("")
            continue

        # Handle headings (#, ##, ###, etc.)
        heading_match = re.match(r'^(#+)\s*(.*)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            if output_format == "txt":
                processed_lines.append(content)
            elif output_format in ["pdf", "docx"]:
                processed_lines.append({"type": "heading", "level": level, "content": content})
            elif output_format == "json":
                processed_lines.append(line)  # Keep Markdown for JSON
            continue

        # Handle bold (**text** or __text__)
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        line = re.sub(r'__(.*?)__', r'\1', line)

        # Handle italic (*text* or _text_)
        line = re.sub(r'\*(.*?)\*', r'\1', line)
        line = re.sub(r'_(.*?)_', r'\1', line)

        # Handle lists (- or *)
        list_match = re.match(r'^[-*]\s+(.*)$', line)
        if list_match:
            content = list_match.group(1).strip()
            if output_format == "txt":
                processed_lines.append(f"- {content}")
            elif output_format in ["pdf", "docx"]:
                processed_lines.append({"type": "list", "content": content})
            elif output_format == "json":
                processed_lines.append(line)
            continue

        # Handle plain text
        if output_format in ["txt", "json"]:
            processed_lines.append(line)
        elif output_format in ["pdf", "docx"]:
            processed_lines.append({"type": "text", "content": line})

    return processed_lines

# Generate comparison analysis table
def generate_comparison_table(original_text, revised_text, ai_analysis, original_filename, revised_filename):
    similarity = calculate_similarity(original_text, revised_text)
    length_change = ((len(revised_text) - len(original_text)) / len(original_text) * 100)
    line_diff = len(revised_text.splitlines()) - len(original_text.splitlines())
    word_diff = len(revised_text.split()) - len(original_text.split())

    # Truncate filenames to avoid overly wide columns
    original_filename = original_filename[:20]  # Limit to 20 chars
    revised_filename = revised_filename[:20]  # Limit to 20 chars

    # Create table data with shorter descriptions
    table_data = [
        {
            "Metric": "Document Names",
            "Original": original_filename,
            "Revised": revised_filename,
            "Description": "Compared document names"
        },
        {
            "Metric": "Length Change",
            "Original": f"{len(original_text):,} chars",
            "Revised": f"{len(revised_text):,} chars",
            "Description": f"{length_change:+.1f}% char change"
        },
        {
            "Metric": "Line Difference",
            "Original": f"{len(original_text.splitlines()):,} lines",
            "Revised": f"{len(revised_text.splitlines()):,} lines",
            "Description": f"{line_diff:+,} lines changed"
        },
        {
            "Metric": "Word Difference",
            "Original": f"{len(original_text.split()):,} words",
            "Revised": f"{len(revised_text.split()):,} words",
            "Description": f"{word_diff:+,} words changed"
        },
    ]
    return table_data

# Generate PDF report
def generate_pdf_report(report_text, original_filename, revised_filename, table_data):
    try:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y_position = height - 40
        left_margin = 40
        max_width = width - 80  # 520 pixels for letter page with 40px margins

        def draw_wrapped_text(text, x, y, font, size, max_width, leading=15):
            c.setFont(font, size)
            words = text.split()
            current_line = ""
            y_pos = y
            for word in words:
                if c.stringWidth(current_line + word + " ", font, size) < max_width:
                    current_line += word + " "
                else:
                    c.drawString(x, y_pos, current_line.strip())
                    y_pos -= leading
                    current_line = word + " "
                    if y_pos < 50:
                        c.showPage()
                        y_pos = height - 40
                        c.setFont(font, size)
            if current_line.strip():
                c.drawString(x, y_pos, current_line.strip())
                y_pos -= leading
            return y_pos

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(left_margin, y_position, "Document Comparison Report")
        y_position -= 30

        # Document info
        c.setFont("Helvetica", 12)
        y_position = draw_wrapped_text(f"Original: {original_filename}", left_margin, y_position, "Helvetica", 12, max_width)
        y_position = draw_wrapped_text(f"Revised: {revised_filename}", left_margin, y_position, "Helvetica", 12, max_width)
        y_position = draw_wrapped_text(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", left_margin, y_position, "Helvetica", 12, max_width)
        y_position -= 20

        # Comparison Table
        c.setFont("Helvetica-Bold", 12)
        y_position = draw_wrapped_text("Comparison Analysis Table", left_margin, y_position, "Helvetica-Bold", 12, max_width)
        y_position -= 10

        # Prepare table data
        table_content = [["Metric", "Original", "Revised", "Description"]]
        for row in table_data:
            table_content.append([
                row["Metric"],
                row["Original"],
                row["Revised"],
                row["Description"][:100]  # Truncate description
            ])

        # Create table with reduced column widths
        col_widths = [80, 120, 120, 130]  # Total = 450 pixels, fits within 520px max_width
        table = Table(table_content, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable word wrapping
        ]))
        table.wrapOn(c, max_width, y_position)
        table_height = table._height
        table.drawOn(c, left_margin, y_position - table_height)
        y_position -= table_height + 20

        # Process Markdown content
        processed_content = process_markdown(report_text, output_format="pdf")
        for item in processed_content:
            if not item:
                y_position -= 15
                continue
            if isinstance(item, dict):
                content = item["content"]
                if item["type"] == "heading":
                    level = item["level"]
                    font_size = 14 if level == 1 else 12 if level == 2 else 10
                    c.setFont("Helvetica-Bold", font_size)
                    y_position = draw_wrapped_text(content, left_margin, y_position, "Helvetica-Bold", font_size, max_width)
                elif item["type"] == "list":
                    c.setFont("Helvetica", 10)
                    y_position = draw_wrapped_text(f"• {content}", left_margin + 10, y_position, "Helvetica", 10, max_width - 10)
                elif item["type"] == "text":
                    c.setFont("Helvetica", 10)
                    y_position = draw_wrapped_text(content, left_margin, y_position, "Helvetica", 10, max_width)
            else:
                c.setFont("Helvetica", 10)
                y_position = draw_wrapped_text(item, left_margin, y_position, "Helvetica", 10, max_width)
            if y_position < 50:
                c.showPage()
                y_position = height - 40

        c.save()
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")
        return None

# Generate DOCX report
def generate_docx_report(report_text, original_filename, revised_filename, table_data):
    try:
        doc = Document()
        
        # Title
        title = doc.add_heading('Document Comparison Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Document info
        doc.add_paragraph(f"Original Document: {original_filename}")
        doc.add_paragraph(f"Revised Document: {revised_filename}")
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Comparison Table
        doc.add_heading('Comparison Analysis Table', level=1)
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ["Metric", "Original", "Revised", "Description"]
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
            hdr_cells[i].paragraphs[0].runs[0].bold = True

        # Set column widths (in centimeters, total ~12cm for narrower table)
        col_widths = [2.5, 3.5, 3.5, 2.5]  # Narrower widths
        for col_idx, width in enumerate(col_widths):
            table.columns[col_idx].width = Cm(width)

        for row in table_data:
            row_cells = table.add_row().cells
            row_cells[0].text = row["Metric"]
            row_cells[1].text = row["Original"]
            row_cells[2].text = row["Revised"]
            row_cells[3].text = row["Description"][:100]  # Truncate description

        # AI Analysis
        doc.add_heading('AI Analysis Results', level=1)
        processed_content = process_markdown(report_text, output_format="docx")
        for item in processed_content:
            if not item:
                doc.add_paragraph("")
                continue
            if isinstance(item, dict):
                content = item["content"]
                if item["type"] == "heading":
                    level = min(item["level"], 3)
                    doc.add_heading(content, level=level)
                elif item["type"] == "list":
                    para = doc.add_paragraph()
                    para.add_run(f"• {content}")
                elif item["type"] == "text":
                    doc.add_paragraph(content)
            else:
                doc.add_paragraph(item)

        # Footer
        footer = doc.add_paragraph('Generated by AI Document Comparator')
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ Error generating DOCX: {str(e)}")
        return None

# Generate JSON report
def generate_json_report(report_text, original_filename, revised_filename, table_data):
    try:
        report_data = {
            "report_metadata": {
                "original_document": original_filename,
                "revised_document": revised_filename,
                "analysis_date": datetime.now().isoformat(),
                "generated_by": "AI Document Comparator"
            },
            "comparison_table": table_data,
            "ai_analysis": report_text,
            "document_stats": {
                "analysis_type": "AI-powered document comparison",
                "comparison_method": "AI analysis"
            }
        }
        buffer = BytesIO()
        buffer.write(json.dumps(report_data, indent=4, ensure_ascii=False).encode('utf-8'))
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"❌ Error generating JSON: {str(e)}")
        return None

# Calculate similarity percentage
def calculate_similarity(text1, text2):
    try:
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return round(matcher.ratio() * 100, 1)
    except:
        return 0.0

# Main application
def main():
    st.markdown("""
    <div class="main-header">
        <h1>🤖 AI Document Comparator</h1>
        <p>Upload any two documents and let AI analyze the differences for you!</p>
    </div>
    """, unsafe_allow_html=True)

    model = initialize_ai()
    if not model:
        st.stop()

    # Sidebar
    with st.sidebar:
        st.markdown("### 🔧 System Status")
        if st.button("🔍 Test API Connection"):
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                st.success("✅ API key found")
                try:
                    genai.configure(api_key=api_key)
                    test_model = genai.GenerativeModel('gemini-2.5-flash')
                    test_response = test_model.generate_content("Test connection.")
                    st.success("✅ API connection successful!")
                except Exception as e:
                    st.error(f"❌ API connection failed: {str(e)}")
            else:
                st.error("❌ No API key found")
        
        st.markdown("### 📋 How to Use")
        st.markdown("""
        1. **Upload Original Document** - First version/baseline document
        2. **Upload Revised Document** - Updated/modified version
        3. **Click Compare** - AI analyzes all differences
        4. **Review Results** - Get comprehensive comparison report
        5. **Download Report** - Save results in multiple formats
        """)
        
        st.markdown("### 📄 Supported Formats")
        st.markdown("- **PDF** (.pdf) - All types of PDF documents")
        st.markdown("- **Word** (.docx) - Microsoft Word documents")
        st.markdown("- **Text** (.txt) - Plain text files")
        st.markdown("- **JSON** (.json) - JSON structured data")
        
        st.markdown("### ⚡ Key Features")
        st.markdown("- **AI-Powered Analysis** - Advanced comparison using Gemini AI")
        st.markdown("- **Comprehensive Reports** - Detailed change analysis with comparison table")
        st.markdown("- **Multiple Export Formats** - PDF, DOCX, TXT, JSON")
        st.markdown("- **Visual Diff View** - Technical line-by-line comparison")
        st.markdown("- **Document Preview** - Side-by-side text view")

    # Main content area
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader("📄 Original Document")
        original_file = st.file_uploader(
            "Choose the original/baseline document",
            type=['pdf', 'docx', 'txt', 'json'],
            key="original",
            help="Upload the first version of your document for comparison"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader("📄 Revised Document") 
        revised_file = st.file_uploader(
            "Choose the revised/updated document",
            type=['pdf', 'docx', 'txt', 'json'],
            key="revised",
            help="Upload the modified version of your document"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    if original_file and revised_file:
        
        # Extract text from documents
        with st.spinner("🔍 Extracting text from documents..."):
            original_text = extract_text(original_file)
            revised_text = extract_text(revised_file)

        if original_text and revised_text:
            # Calculate metrics
            similarity = calculate_similarity(original_text, revised_text)
            length_change = ((len(revised_text) - len(original_text)) / len(original_text) * 100)
            
            # Document information
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="success-box">
                    <h4>📄 Original Document</h4>
                    <strong>File:</strong> {original_file.name}<br>
                    <strong>Size:</strong> {len(original_text):,} characters<br>
                    <strong>Lines:</strong> {len(original_text.splitlines()):,}<br>
                    <strong>Words:</strong> {len(original_text.split()):,}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="success-box">
                    <h4>📄 Revised Document</h4>
                    <strong>File:</strong> {revised_file.name}<br>
                    <strong>Size:</strong> {len(revised_text):,} characters<br>
                    <strong>Lines:</strong> {len(revised_text.splitlines()):,}<br>
                    <strong>Words:</strong> {len(revised_text.split()):,}
                </div>
                """, unsafe_allow_html=True)

            # Comparison metrics
            st.markdown(f"""
            <div class="metric-container">
                <h4>📊 Quick Metrics</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div><strong>Similarity:</strong> {similarity}%</div>
                    <div><strong>Length Change:</strong> {length_change:+.1f}%</div>
                    <div><strong>Size Difference:</strong> {len(revised_text) - len(original_text):+,} chars</div>
                    <div><strong>Line Difference:</strong> {len(revised_text.splitlines()) - len(original_text.splitlines()):+,}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Compare button
            if st.button("🔍 **COMPARE DOCUMENTS**", type="primary", use_container_width=True):
                with st.spinner("🤖 AI is analyzing the differences... This may take a moment."):
                    # Generate comparison table
                    table_data = generate_comparison_table(
                        original_text,
                        revised_text,
                        "",  # Placeholder for ai_analysis as it's not yet available
                        original_file.name,
                        revised_file.name
                    )
                    st.session_state['table_data'] = table_data
                    
                    # Perform AI analysis
                    ai_analysis = compare_documents_ai(original_text, revised_text, model)
                    if ai_analysis:
                        st.session_state['analysis'] = ai_analysis
                        st.session_state['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Display comparison results if available in session state
            if 'analysis' in st.session_state and 'table_data' in st.session_state:
                st.markdown('<div class="comparison-result">', unsafe_allow_html=True)
                
                # Display comparison table at the start
                st.markdown("## 📊 Comparison Analysis Table")
                st.dataframe(st.session_state['table_data'], use_container_width=True)
                
                # Display AI analysis results
                st.markdown("## 🤖 AI Analysis Results")
                st.markdown('<div class="difference-box">', unsafe_allow_html=True)
                st.markdown(st.session_state['analysis'])
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Document Preview Section
            st.markdown("## 📖 Document Preview")
            
            preview_col1, preview_col2 = st.columns(2)
            with preview_col1:
                st.markdown("### Original Document")
                st.text_area(
                    "Original Content",
                    original_text,
                    height=400,
                    disabled=False,
                    key="original_preview"
                )
            
            with preview_col2:
                st.markdown("### Revised Document") 
                st.text_area(
                    "Revised Content",
                    revised_text,
                    height=400,
                    disabled=False,
                    key="revised_preview"
                )
            
            # Download Section
            if 'analysis' in st.session_state and 'table_data' in st.session_state:
                st.markdown("## 💾 Download Analysis Report")
                
                table_data = st.session_state['table_data']
                ai_analysis = st.session_state['analysis']
                analysis_date = st.session_state.get('analysis_date', 'N/A')
                
                # Generate report text for TXT
                table_text = "\nCOMPARISON ANALYSIS TABLE:\n"
                table_text += f"{'Metric':<15} {'Original':<20} {'Revised':<20} {'Description':<25}\n"
                table_text += "-" * 80 + "\n"
                for row in table_data:
                    table_text += f"{row['Metric'][:15]:<15} {row['Original'][:20]:<20} {row['Revised'][:20]:<20} {row['Description'][:25]:<25}\n"

                report_text_txt = f"""Document Comparison Report

Original Document: {original_file.name}
Revised Document: {revised_file.name}
Analysis Date: {analysis_date}
Generated By: AI Document Comparator

COMPARISON METRICS:
- Similarity: {similarity}%
- Length Change: {length_change:+.1f}%
- Character Difference: {len(revised_text) - len(original_text):+,}
- Line Difference: {len(revised_text.splitlines()) - len(original_text.splitlines()):+,}

{table_text}
AI ANALYSIS:
{'\n'.join(process_markdown(ai_analysis, output_format='txt'))}
"""
                
                # Use raw Markdown for PDF and DOCX
                report_text_formatted = f"""Document Comparison Report

Original Document: {original_file.name}
Revised Document: {revised_file.name}
Analysis Date: {analysis_date}
Generated By: AI Document Comparator

COMPARISON METRICS:
- Similarity: {similarity}%
- Length Change: {length_change:+.1f}%
- Character Difference: {len(revised_text) - len(original_text):+,}
- Line Difference: {len(revised_text.splitlines()) - len(original_text.splitlines()):+,}

AI ANALYSIS:
{ai_analysis}
"""
                
                # Download buttons
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.download_button(
                        label="📄 Download TXT",
                        data=report_text_txt,
                        file_name=f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col2:
                    pdf_buffer = generate_pdf_report(report_text_formatted, original_file.name, revised_file.name, table_data)
                    if pdf_buffer:
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_buffer,
                            file_name=f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                
                with col3:
                    docx_buffer = generate_docx_report(report_text_formatted, original_file.name, revised_file.name, table_data)
                    if docx_buffer:
                        st.download_button(
                            label="📄 Download DOCX",
                            data=docx_buffer,
                            file_name=f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                
                with col4:
                    json_buffer = generate_json_report(report_text_formatted, original_file.name, revised_file.name, table_data)
                    if json_buffer:
                        st.download_button(
                            label="📄 Download JSON",
                            data=json_buffer,
                            file_name=f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )

    else:
        st.markdown("""
        <div class="warning-box">
            <h4>⏳ Ready to Compare Documents</h4>
            Please upload both documents (original and revised versions) to begin the AI-powered comparison analysis.
            <br><br>
            <strong>Supported file types:</strong> PDF, DOCX, TXT, JSON<br>
            <strong>Analysis includes:</strong> Content changes, structural differences, impact assessment, comparison table, and detailed recommendations.
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem; padding: 1rem;">
        <p><strong>🤖 AI Document Comparator</strong> | Powered by Google Gemini AI | Built with Streamlit</p>
        <p>Compare any documents - contracts, reports, articles, code, essays, manuals, JSON data, and more!</p>
        <p><em>Universal document comparison for all your analysis needs</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()