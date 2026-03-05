import pathlib

import streamlit as st


def page_config(title):
    st.set_page_config(
        page_title=title, page_icon=f"{pathlib.Path().resolve()}/static/favicon.ico"
    )
