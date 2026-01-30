"""Streamlit UI for SQL visualization."""

import json
import streamlit as st

from sqlviz.errors import ParseError, SQLVizError, UnsupportedSQLError
from sqlviz.model import build_graph
from sqlviz.parser import parse_sql
from sqlviz.renderer import render_graph

# Page configuration
st.set_page_config(page_title="SQL Visualizer", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS: shiny black background, centered purple glass title
st.markdown(
    """
    <style>
    /* Shiny black background */
    .stApp {
        background: linear-gradient(145deg, #0a0a0f 0%, #1a1a24 50%, #0d0d12 100%);
        background-attachment: fixed;
    }
    /* Center title and subtitle with liquid glass Mac feel */
    .main-title-block {
        text-align: center;
        padding: 2rem 0 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .main-title {
        display: block;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
        font-size: 2.75rem;
        font-weight: 700;
        background: linear-gradient(110deg, #c4b5fd 0%, #a78bfa 20%, #e9d5ff 40%, #a78bfa 60%, #8b5cf6 80%, #c4b5fd 100%);
        background-size: 300% 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.02em;
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.5))
                drop-shadow(0 0 24px rgba(139, 92, 246, 0.5))
                drop-shadow(0 0 48px rgba(167, 139, 250, 0.35));
        animation: title-shine 4s ease-in-out infinite;
    }
    @keyframes title-shine {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    .main-subtitle {
        display: block;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
        font-size: 0.1rem;
        color: rgba(196, 181, 253, 0.9);
        margin-top: 0.5rem;
        font-weight: 300;
        letter-spacing: 0.01em;
        width: 100%;
    }
    /* SQL Query text area - no borders */
    .stTextArea textarea, .stTextArea label, .stTextArea div {
        background-color: rgba(30, 30, 40, 0.8) !important;
        color: #e2e8f0 !important;
        border-radius: 12px;
        border: none !important;
        box-shadow: none !important;
    }
    .stTextArea textarea:focus {
        border: none !important;
        box-shadow: none !important;
    }
    /* Visualize and Clear buttons - no borders */
    .stButton > button {
        border-radius: 10px;
        border: none !important;
        box-shadow: none !important;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(167, 139, 250, 0.15));
        color: #c4b5fd;
        font-weight: 500;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.35), rgba(167, 139, 250, 0.25));
        border: none !important;
        color: #e9d5ff;
    }
    /* Query Details expander - white text, no borders */
    [data-testid="stExpander"] details {
        border: none !important;
        background-color: rgba(30, 30, 40, 0.6) !important;
        border-radius: 12px;
    }
    [data-testid="stExpander"] summary {
        color: rgba(196, 181, 253, 0.95) !important;
        border: none !important;
    }
    [data-testid="stExpander"] div {
        color: #ffffff !important;
        border: none !important;
    }
    [data-testid="stExpander"] pre, [data-testid="stExpander"] code,
    .streamlit-expanderContent pre, .streamlit-expanderContent code,
    .streamlit-expanderContent {
        color: #e2e8f0 !important;
        background: rgba(30, 30, 40, 0.8) !important;
        border: none !important;
    }
    /* Diagram section heading */
    h3 {
        color: rgba(196, 181, 253, 0.95) !important;
        font-weight: 600;
    }
    /* Footer text */
    small {
        color: rgba(148, 163, 184, 0.8) !important;
    }
    hr {
        border-color: rgba(139, 92, 246, 0.2) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Centered title and subtitle (liquid glass Mac feel)
st.markdown(
    '<div class="main-title-block">'
    '<h1 class="main-title">SQL Query Visualizer</h1>'
    '<p class="main-subtitle">Convert SQL queries into visual diagrams</p>'
    '</div>',
    unsafe_allow_html=True,
)

# Initialize session state
if "sql_input" not in st.session_state:
    st.session_state.sql_input = ""
if "last_parsed" not in st.session_state:
    st.session_state.last_parsed = None
if "last_svg" not in st.session_state:
    st.session_state.last_svg = None

# SQL input area
sql_input = st.text_area(
    "Enter SQL Query",
    value=st.session_state.sql_input,
    height=200,
    placeholder="SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id WHERE users.active = 1",
    help="Supports: SELECT, FROM, INNER JOIN, LEFT JOIN, WHERE, GROUP BY",
)

# Buttons
col1, col2 = st.columns(2)

with col1:
    visualize_btn = st.button("Visualize", type="primary", use_container_width=True)

with col2:
    clear_btn = st.button("Clear", use_container_width=True)

if clear_btn:
    st.session_state.sql_input = ""
    st.session_state.last_parsed = None
    st.session_state.last_svg = None
    st.rerun()

# Update session state
st.session_state.sql_input = sql_input

# Process visualization
if visualize_btn and sql_input:
    try:
        parsed = parse_sql(sql_input)
        graph = build_graph(parsed)
        try:
            svg = render_graph(graph)
            if not svg or len(svg.strip()) == 0:
                st.error("Failed to generate diagram. SVG is empty.")
            elif not svg.startswith("<svg"):
                st.error(f"Invalid SVG output. Got: {svg[:200]}")
            else:
                st.session_state.last_parsed = parsed
                st.session_state.last_svg = svg
        except ValueError as e:
            st.error(f"Rendering error: {str(e)}")
    except UnsupportedSQLError as e:
        st.error(f"Unsupported SQL feature: {e.message}")
    except ParseError as e:
        st.error(f"Parse error: {e.message}")
    except SQLVizError as e:
        st.error(f"Error: {str(e)}")
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
elif visualize_btn:
    st.warning("Please enter a SQL query to visualize")

# Show diagram and Query Details from session state (persists across reruns)
if st.session_state.last_svg and st.session_state.last_parsed is not None:
    st.markdown("### Diagram")
    import base64
    svg_b64 = base64.b64encode(st.session_state.last_svg.encode("utf-8")).decode("utf-8")
    st.markdown(
        f'<div style="text-align: center; width: 100%; padding: 1rem 0;">'
        f'<img src="data:image/svg+xml;base64,{svg_b64}" style="max-width: 100%; height: auto; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">'
        f'</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Query Details"):
        # Use st.code so content is visible (st.json can be empty/hidden with custom CSS)
        parsed = st.session_state.last_parsed
        json_str = json.dumps(parsed, indent=2, default=str)
        st.code(json_str, language="json")

# Footer
st.markdown("---")
st.markdown(
    "<small>Supports: SELECT, FROM, INNER JOIN, LEFT JOIN, WHERE, GROUP BY</small>",
    unsafe_allow_html=True,
)
