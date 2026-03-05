from typing import List

import streamlit as st

from backend_func import (
    Image,
    restore_image,
    accept_image,
    reject_image as reject_image_st,
    set_comment,
)

payload_statuses = {
    "accepted": "Принято",
    "pending": "В ожидании",
    "edited": "Отредактировано",
    "rejected": "Требует редактирования",
}


@st.dialog("Почему эта фотография не подходит?")
def reject_image(image_id: str, image_status: str, payload_id: int):
    reason = st.text_input(label="Сообщение для врача", placeholder="Введите сообщение", max_chars=150)
    if st.button("Отклонить"):
        if reason.strip() == "":
            st.error("Введите сообщение для врача")
            return
        reject_image_st(image_id, image_status, payload_id)
        if reason is not None:
            set_comment(image_id, reason)
        st.rerun()


def images_list(
    images: List[Image], payload, is_archive: bool = False, is_accepted: bool = False, is_case=False
):
    display_columns = st.number_input("Количество колонок:", 1, 5, 3)
    cols = None

    for i, image in enumerate(images):
        if i % display_columns == 0:
            cols = st.columns(display_columns)

        with cols[i % display_columns]:
            try:
                st.image(image.bytes)
            except Exception as e:
                print(e)
                st.caption("Невозможно отобразить картинку")

            kwargs = {
                "image_id": image.id,
                "image_status": image.status,
                "payload_id": payload["id"],
            }

            if is_archive:
                st.button(
                    "Восстановить", key=image.id, on_click=restore_image, kwargs=kwargs
                )
            elif not is_accepted:
                accept_key = f"accept_btn{image.id}"
                reject_key = f"reject_btn{image.id}"

                c1, c2 = st.columns(2)
                c1.button(
                    "Принять", key=accept_key, on_click=accept_image, kwargs=kwargs
                )
                c2.button(
                    "Отклонить", key=reject_key, on_click=reject_image, kwargs=kwargs
                )
            if is_accepted and is_case:
                image_status = payload_statuses[image.status]
                st.error(image_status) if image.status == 'rejected' else st.warning(image_status) if image.status == 'edited' else st.info(image_status) if image.status == 'pending' else st.success(image_status)
