import os
import pathlib
from urllib.parse import urlencode

from streamlit.runtime import Runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx

import streamlit as st

from config import Config


def _get_session_id():
    context = get_script_run_ctx()
    if not context:
        return
    return context.session_id


def _get_current_request():
    session_id = _get_session_id()
    if not session_id:
        return None
    runtime = Runtime._instance
    if not runtime:
        return
    client = runtime.get_client(session_id)
    if not client:
        return
    return client.request


def get_web_origin():
    request = _get_current_request()
    return request.headers["Origin"] if request else os.getenv("WEB_BASE", "")


def logout(theme):
    if (
        not theme
        or "keycloak" not in st.session_state
        or not st.session_state.keycloak.user_info
    ):
        return

    params = urlencode(
        {
            "post_logout_redirect_uri": get_web_origin(),
            "id_token_hint": st.session_state.keycloak.id_token,
        }
    )

    icon = open(f"{pathlib.Path().resolve()}/static/logout", "r")

    st.markdown(
        f"""
            <a target="_self" href="{Config.KEYCLOAK_URL}/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/logout?{params}" style="color:{theme["textColor"]};text-decoration:none;display:block;margin-bottom:20px">
                <svg width="50" height="50" viewBox="0 0 50 50" fill="none" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
                    <mask id="mask0_22_1039" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="0" y="0" width="50" height="50">
                        <rect width="50" height="50" fill="url(#pattern0_22_1039)"/>
                    </mask>
                    <g mask="url(#mask0_22_1039)">
                        <rect x="2" y="1" width="47" height="47" fill="{theme["textColor"]}"/>
                    </g>
                    <defs>
                        <pattern id="pattern0_22_1039" patternContentUnits="objectBoundingBox" width="1" height="1">
                            <use xlink:href="#image0_22_1039" transform="scale(0.00195312)"/>
                        </pattern>
                        <image id="image0_22_1039" width="512" height="512" xlink:href="{icon.read()}"/>
                    </defs>
                </svg>
                Выйти из аккаунта
            </a>
        """,
        unsafe_allow_html=True,
    )

    icon.close()
