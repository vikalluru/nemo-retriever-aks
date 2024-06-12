import streamlit as st

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to Nvidia NIM demo collection! 👋")

st.sidebar.success("Select a demo above.")

footer = """
<style>
.footer {
    position: fixed;
    bottom: 0;
    width: 100%;
    color: white;
    text-align: center;
    padding: 10px;
    font-size: 14px;
}
</style>
<div class="footer">
<p>Developed with ❤ by Vineeth Kalluru :)</p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)
