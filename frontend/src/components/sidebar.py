import streamlit as st

from backend_func import get_payloads, get_payloads_count
from components.logout import logout
from components.nav import nav
from components.payload import payload
from components.pagination import pagination
from config import Config
from utils import decl

status_payload = {
    "В ожидании": "pending",
    "Приняты": "accepted",
    "Отклонены": "edited",
    "Нужно исправить": "rejected",
}


def sidebar(
    theme,
    location,
    display_logout: bool = False,
    display_payloads: bool = False,
    display_nav: bool = False,
    disable_edit=False,
):
    if "history_page" not in st.session_state:
        st.session_state["history_page"] = 1

    if "filter_payload" not in st.session_state:
        st.session_state.filter_payload = []

    def update_selection():
        current_selection = st.session_state.filter_payload
        if len(current_selection) > 1:
            st.session_state.filter_payload = current_selection[-1:]

    with st.sidebar:
        if display_logout:
            logout(theme)

        if display_nav:
            nav()

        if display_payloads:
            payloads = get_payloads(
                limit=Config.HISTORY_PAGINATION_AMOUNT,
                page=st.session_state.history_page,
            )
            payloads.reverse()
            amount = get_payloads_count()
            if not disable_edit:
                st.multiselect(
                    "Выбрать фильтр",
                    ["В ожидании", "Приняты", "Отклонены", "Нужно исправить"],
                    placeholder="Выберите фильтр",
                    on_change=update_selection,
                    key="filter_payload",
                )
            if st.button("Обновить историю"):
                st.rerun()
            pagination(
                total=amount, on_page=Config.HISTORY_PAGINATION_AMOUNT, page="history"
            )
            if not st.session_state.filter_payload:
                filtered_payloads = payloads
            else:
                filtered_payloads = [
                    p
                    for p in payloads
                    if p["status"] in status_payload[st.session_state.filter_payload[0]]
                ]

            for parcel in filtered_payloads:
                payload(
                    payload_id=parcel["id"],
                    amount=str(parcel["amount"])
                    + decl(parcel["amount"], [" файл", " файла", " файлов"]),
                    date=parcel["time"],
                    status="accepted" if disable_edit else parcel["status"],
                    theme=theme,
                    location=location,
                )
            pagination(
                total=amount,
                on_page=Config.HISTORY_PAGINATION_AMOUNT,
                page="history",
                duplicate=True,
            )
