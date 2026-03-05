import streamlit as st
from streamlit_js_eval import get_page_location
from streamlit_theme import st_theme

from components.file_uploader_segment import file_uploader_segment
from components.localization import localization
from components.authenticate import authenticate
from backend_func import get_duplicate_name, create_payload_divided_stage
from components.page_config import page_config
from components.sidebar import sidebar
from utils import is_divided_into_stages, decl, get_metadata


def get_image_info_from_files(files_before, files_coloring, files_after, files_other):
    try:
        images_before = get_metadata(files_before)
        images_coloring = get_metadata(files_coloring)
        images_after = get_metadata(files_after)
        image_other = get_metadata(files_other)
        hashes = (
            list(images_after.keys())
            + list(images_coloring.keys())
            + list(images_before.keys())
            + list(image_other.keys())
        )

        if len(hashes) != len(set(hashes)):
            raise ValueError

        return False, images_before, images_coloring, images_after, image_other
    except ValueError:
        return True, None, None, None, None


def get_toast_message(payload_ids):
    return (f"{decl(len(payload_ids), ['Отправлена', 'Отправлены', 'Отправлены'])} {decl(len(payload_ids), ['посылка', 'посылки', 'посылок'])} с "
            f"{decl(len(payload_ids), ['номером', 'номерами', 'номерами'])}: {', '.join(payload_ids)}")


def send_payload(patient_id, age, sex, files_before, files_coloring, files_after, files_other):
    if patient_id == "":
        st.error("Введите идентификатор пациента")
        return

    if age is None:
        st.error("Введите возраст пациента")
        return

    if sex is None:
        st.error("Введите пол пациента")
        return

    if len(files_after) + len(files_coloring) + len(files_before) + len(files_other) == 0:
        st.error("Прикрепите фотографии")
        return
    (contains_duplicates, images_before, images_coloring, images_after, images_other) = (
        get_image_info_from_files(
            files_before=files_before,
            files_coloring=files_coloring,
            files_after=files_after,
            files_other=files_other
        )
    )

    if contains_duplicates:
        st.error("Одна и та же фотография прикреплена несколько раз")
        return

    duplicate = get_duplicate_name(images_after)

    if duplicate is None:
        duplicate = get_duplicate_name(images_coloring)

    if duplicate is None:
        duplicate = get_duplicate_name(images_before)

    if duplicate is None:
        duplicate = get_duplicate_name(images_other)

    if duplicate is not None:
        st.error(f"Изображение {duplicate} уже есть в базе данных")
        return

    payload_ids = create_payload_divided_stage(
        patient_id=patient_id,
        age=age,
        sex="male" if sex == "Мужской" else "female",
        images_before=images_before,
        images_coloring=images_coloring,
        images_after=images_after,
        images_other=images_other,
    )

    st.session_state.sent_payloads_ids.extend(payload_ids)
    st.session_state.toast_message = get_toast_message(payload_ids)
    st.session_state.payload_number += 1
    st.rerun()


# Title and favicon
page_config("Загрузка")


# Translation
localization()


# Authentication and authorization
authenticate()

if "keycloak_roles" not in st.session_state:
    st.stop()

if not is_divided_into_stages():
    st.switch_page("main.py")


# State init
if (
    "contains_bad_photos" not in st.session_state
    or st.session_state.contains_bad_photos
):
    st.session_state.contains_bad_photos = False

if "payload_number" not in st.session_state:
    st.session_state.payload_number = 1

if "toast_message" not in st.session_state:
    st.session_state.toast_message = None

if "sent_payloads_ids" not in st.session_state:
    st.session_state.sent_payloads_ids = []


# Sidebar
theme = st_theme()
location = get_page_location()
sidebar(
    theme=theme,
    location=location,
    display_logout=True,
    display_payloads=True,
)


# Toast
if st.session_state.toast_message:
    st.toast(st.session_state.toast_message)
    st.session_state.toast_message = None


# Page
st.title("Создание посылки")

patient_id = st.text_input(
    label="Пациент",
    placeholder="Идентификатор пациента",
    key=f"pid{st.session_state.payload_number}",
)

age = st.number_input(
    label="Возраст",
    placeholder="От 4 до 18 лет",
    value=None,
    min_value=4,
    max_value=18,
    step=1,
    key=f"age{st.session_state.payload_number}",
)

sex = st.selectbox(
    label="Пол",
    placeholder="Выберите вариант",
    index=None,
    options=["Женский", "Мужской"],
    key=f"sex{st.session_state.payload_number}",
)

(files_before, contains_bad_photos_before) = file_uploader_segment("До гигиены")
(files_coloring, contains_bad_photos_coloring) = file_uploader_segment(
    "После окрашивания налёта"
)
(files_after, contains_bad_photos_after) = file_uploader_segment("После гигиены")

(files_other, contains_bad_photos_other) = file_uploader_segment("Фотографии с разного ракурса")

total_photos = len(files_before) + len(files_coloring) + len(files_after) + len(files_other)
button_label = f"Отправить ({total_photos} фото)"

if st.button(button_label):
    if (
        contains_bad_photos_before
        or contains_bad_photos_coloring
        or contains_bad_photos_after
        or contains_bad_photos_other
    ):
        st.error("Посылка содержит битые файлы")
    else:
        send_payload(
            patient_id=patient_id,
            age=age,
            sex=sex,
            files_before=files_before,
            files_coloring=files_coloring,
            files_after=files_after,
            files_other=files_other,
        )
