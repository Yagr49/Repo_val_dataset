import streamlit as st
from streamlit import rerun
from streamlit_js_eval import get_page_location
from streamlit_theme import st_theme

from components.images_list import images_list
from components.authenticate import authenticate
from backend_func import (
    get_all_payloads_st,
    get_payload,
    payload_stages,
    get_payloads_case_id,
    mapping_group_payload
)
from components.page_config import page_config
from components.payloads_display import payloads_display
from components.sidebar import sidebar
from components.pagination import pagination
from components.case_payload_display import case_payload_display
from utils import is_admin, is_image_status_accepted

# Title and favicon
page_config("Принято")

# Authentication and authorization
authenticate()

if "keycloak_roles" not in st.session_state:
    st.stop()

if not is_admin():
    st.switch_page("main.py")


# State init
if "active_uploaded_payload" not in st.session_state:
    st.session_state.active_uploaded_payload = None

if "is_diag_opened" in st.session_state:
    st.session_state["is_diag_opened"] = False

if "choise_case_payload_accept" not in st.session_state:
    st.session_state.choise_case_payload_accept = None


def set_uploaded_payload(payload):
    st.session_state.active_uploaded_payload = payload


def set_case_payloads(case_id):
    st.session_state.choise_case_payload_accept = case_id


# Sidebar
theme = st_theme()
location = get_page_location()
sidebar(theme=theme, location=location, display_logout=True, display_nav=True)


# Page
if (st.session_state.active_uploaded_payload is None) and (
    st.session_state.choise_case_payload_accept is None
):
    payloads = [
        payload
        for payload in get_all_payloads_st("accepted")
        if "accepted" in payload["pages"]
    ]

    st.header("Принятые изображения")

    if len(payloads) != 0:
        page = pagination(len(payloads), "accepted")
        payloads_display(
            payloads,
            set_uploaded_payload,
            set_case_payloads,
            is_accepted=True,
            page=page,
        )
        pagination(len(payloads), "accepted", True)
    else:
        st.divider()
        st.write("На данный момент здесь нет посылок")
elif (st.session_state.active_uploaded_payload is not None) and (
    st.session_state.choise_case_payload_accept is None
):
    payload = get_payload(st.session_state.active_uploaded_payload["id"])
    if st.button("Назад"):
        st.session_state.active_uploaded_payload = None
        st.rerun()

    st.header(f"Посылка №{payload['id']}")
    st.write(f"{mapping_group_payload.get(payload['payload_case'], '')}")
    st.write(payload["doctor"])
    st.write(payload_stages[payload["payload_stage"]])

    images = [
        image for image in payload["images"] if is_image_status_accepted(image.status)
    ]
    if len(images) == 0:
        st.session_state.active_uploaded_payload = None
        rerun()

    images_list(images, payload, is_accepted=True)
else:
    if st.session_state.active_uploaded_payload is None:
        try:
            payloads_by_case = get_payloads_case_id(
                st.session_state.choise_case_payload_accept
            )
        except Exception as e:
            print(e)
            st.error("Произошла ошибка при получении посылок кейса.")

        if st.button("Назад"):
            st.session_state.choise_case_payload_accept = None
            st.rerun()
        case_payload_display(payloads_by_case, set_uploaded_payload)
    else:
        payload = get_payload(st.session_state.active_uploaded_payload["id"])
        if st.button("Назад"):
            st.session_state.active_uploaded_payload = None
            st.rerun()

        st.header(f"Посылка №{payload['id']}")
        st.write(f"{mapping_group_payload.get(payload['payload_case'], '')}")
        st.write(payload["doctor"])
        st.write(payload_stages[payload["payload_stage"]])

        images = [image for image in payload["images"]]
        if len(images) == 0:
            st.session_state.active_uploaded_payload = None
            rerun()

        images_list(images, payload, is_accepted=True, is_case=True)
