import streamlit as st
from backend_func import payload_stages, mapping_group_payload
from config import Config

PAYLOADS_ON_PAGE = Config.PAGINATION_AMOUNT

payload_statuses = {
    "accepted": "Принято",
    "pending": "В ожидании",
    "edited": "Отредактировано",
    "rejected": "Требует редактирования",
}

if "active_uploaded_payload_case" not in st.session_state:
    st.session_state.active_uploaded_payload_case = None


def case_payload_display(payloads, set_active_payload, page=1):
    n_columns = 3
    columns = None

    for i, payload in enumerate(payloads[(page-1)*PAYLOADS_ON_PAGE:page*PAYLOADS_ON_PAGE]):
        if i % n_columns == 0:
            columns = st.columns(n_columns)

        column = columns[i % n_columns]

        payload_status = payload_statuses[payload['status']]

        container = column.container(border=True, height=450)
        container.subheader(f"Посылка №{payload['id']}")
        container.write(f"{mapping_group_payload.get(payload['payload_case'], '')}")
        container.write("Статус посылки: ")
        container.error(payload_status) if payload["status"] == 'rejected' else container.warning(payload_status) if payload["status"] == 'edited' else container.info(payload_status) if payload["status"] == 'pending' else container.success(payload_status)
        container.write(payload["doctor"])
        container.write(payload_stages[payload["payload_stage"]])
        container.button(
            f"Просмотреть {payload['images_count']} фото",
            key=f"photos_{payload['id']}",
            on_click=set_active_payload,
            kwargs={"payload": payload},
        )
