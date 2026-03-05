from streamlit_keycloak import login
import streamlit as st

from config import Config
from utils import get_roles, get_user_info
from background_tasks import run_background_processor


def authenticate():
    keycloak = login(
        url=Config.KEYCLOAK_URL,
        realm=Config.KEYCLOAK_REALM,
        client_id=Config.KEYCLOAK_FRONTEND_CLIENT,
        init_options={"checkLoginIframe": False},
        custom_labels={
            "labelButton": "Войти",
            "labelLogin": "Пожалуйста, войдите в ваш аккаунт.",
            "errorNoPopup": "Не удалось открыть окно авторизации. Попробуйте разрешить всплывающие окна и перезагрузить сайт.",
            "errorPopupClosed": "Вы закрыли страницу авторизации.",
            "errorFatal": "Не удалось подключиться к серверу авторизации.",
        },
    )
    if keycloak.authenticated:
        st.session_state.keycloak = keycloak
        st.session_state.keycloak_roles = get_roles(keycloak.access_token)
        st.session_state.user_info = get_user_info(keycloak.access_token)

    run_background_processor()
