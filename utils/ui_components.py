
import streamlit as st


def load_css():
    """Load custom CSS from file"""
    try:
        with open('style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def styled_title(text: str, level: int = 1):
    """Display a styled title with rounded corners and custom background color
    
    Args:
        text: The title text
        level: Heading level (1, 2, or 3 for h1, h2, or h3)
    """
    tag = f"h{level}"
    st.markdown(f"""
        <div class="styled-title">
            <{tag}>{text}</{tag}>
        </div>
    """, unsafe_allow_html=True)

def create_info_box(text: str, box_type: str = "info"):
    """Create an information box with styling
    
    Args:
        text: The text to display
        box_type: Type of box (info, warning, error, success)
    """
    color_map = {
        "info": "#d1ecf1",
        "warning": "#fff3cd",
        "error": "#f8d7da",
        "success": "#d4edda"
    }

    color = color_map.get(box_type, color_map["info"])

    st.markdown(f"""
        <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 10px 0;">
            {text}
        </div>
    """, unsafe_allow_html=True)
