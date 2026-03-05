import streamlit as st

from utils import is_admin


def nav():
    with st.sidebar:
        if is_admin():
            st.page_link("pages/accepted.py", label="Принятые фотографии")
            st.page_link("pages/verification.py", label="Верификация")
            st.page_link("pages/archive.py", label="Архив")
            st.page_link("pages/stats.py", label="Статистика")
            st.page_link("pages/upload_admin.py", label="Отправка посылок")
            # st.link_button("Export", "https://www.google.com/")
