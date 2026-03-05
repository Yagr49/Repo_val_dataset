import streamlit as st
from backend_func import payload_stages, mapping_group_payload
from config import Config

PAYLOADS_ON_PAGE = Config.PAGINATION_AMOUNT


def set_case_url(case_id):
    st.query_params["case_id"] = case_id


def case_button_click(case_id, set_case_payloads_func):
    set_case_payloads_func(case_id)
    set_case_url(case_id=case_id)


def payloads_display(
    payloads,
    set_active_payload,
    set_case_payloads,
    is_archive=False,
    is_accepted=False,
    page=1,
):
    n_columns = 3
    columns = None
    for i, payload in enumerate(
        payloads[(page - 1) * PAYLOADS_ON_PAGE:page * PAYLOADS_ON_PAGE]
    ):
        if i % n_columns == 0:
            columns = st.columns(n_columns)

        column = columns[i % n_columns]
        countable_statuses = (
            "rejected" if is_archive else "accepted" if is_accepted else "pending"
        )
        photos_amount = len(
            [
                image
                for image in payload["images"]
                if image["status"] in countable_statuses
            ]
        )
        container = column.container(border=True, height=370)
        container.subheader(f"Посылка №{payload['id']}")
        container.write(f"{mapping_group_payload.get(payload['payload_case'], '')}")
        container.write(payload["doctor"])
        container.write(payload_stages[payload["payload_stage"]])
        container.button(
            f"Просмотреть {photos_amount} фото",
            key=f"photos_{payload['id']}",
            on_click=set_active_payload,
            kwargs={"payload": payload},
        )

        container.button(
            "Просмотреть кейс",
            key=f"case_{payload['patient']}_{payload['id']}",
            on_click=case_button_click,
            kwargs={
                "case_id": payload["case_id"],
                "set_case_payloads_func": set_case_payloads,
            },
        )
