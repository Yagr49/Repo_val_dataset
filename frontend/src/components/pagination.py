import math

import streamlit as st

from config import Config

PAYLOADS_ON_PAGE = Config.PAGINATION_AMOUNT


def pagination(total: int, page: str, duplicate: bool = False, on_page=None):
    def set_page(n: int):
        st.session_state[f"{page}_page"] = n

    if f"{page}_page" not in st.session_state:
        st.session_state[f"{page}_page"] = 1

    max_page = math.ceil(total / on_page if on_page is not None else PAYLOADS_ON_PAGE)
    current_page = st.session_state[f"{page}_page"]
    cols = st.columns(7)
    cols[0].button("<", disabled=current_page <= 1, on_click=set_page, args=[current_page-1], key=f"<_{duplicate}")

    start = current_page - 2 if current_page > 3 else 1

    for i in range(1, 6):
        page_n = start + i - 1
        if page_n > max_page:
            continue
        cols[i].button(str(page_n), on_click=set_page, args=[page_n], key=f"{page_n}_{duplicate}", disabled=current_page == page_n)

    cols[6].button(r"\>", disabled=current_page >= max_page, on_click=set_page, args=[current_page+1], key=f">_{duplicate}")

    return current_page
