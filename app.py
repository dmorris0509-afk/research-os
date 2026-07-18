import streamlit as st

st.set_page_config(
    page_title="Research OS",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Research OS")

st.markdown("""
### Constitutional Research Operating System

Transforming:

**Question → Evidence → Analysis → Knowledge**
""")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Research Modules",
    [
        "Home",
        "Research Intake",
        "Evidence",
        "Analysis",
        "Knowledge",
        "Verification",
        "Publication",
    ],
)

st.write(f"Current Module: **{page}**")
