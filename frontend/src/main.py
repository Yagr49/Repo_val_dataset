import pathlib

import streamlit as st
from streamlit_theme import st_theme

from components.authenticate import authenticate
from components.logout import logout
from utils import is_admin, is_divided_into_stages, is_without_splitting

# Title and favicon
st.set_page_config(
    page_title="Вход", page_icon=f"{pathlib.Path().resolve()}/static/favicon.ico"
)


# Authentication
authenticate()

# Authorization
if is_admin():
    st.switch_page("pages/verification.py")
elif is_divided_into_stages():
    st.switch_page("pages/upload.py")
elif is_without_splitting():
    st.switch_page("pages/upload_clinic2.py")
else:
    theme = st_theme()
    logout(theme)
    if "keycloak" in st.session_state and st.session_state.keycloak.authenticated:
        st.warning("У пользователя недостаточно прав для доступа к сервису")
