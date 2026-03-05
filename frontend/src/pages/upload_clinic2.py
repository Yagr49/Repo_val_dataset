import datetime

import streamlit as st
from streamlit_js_eval import get_page_location
from streamlit_theme import st_theme

from components.file_uploader_segment import file_uploader_segment
from components.localization import localization
from components.authenticate import authenticate
from backend_func import get_duplicate_name, upload_images
from components.page_config import page_config
from components.sidebar import sidebar
from utils import get_patient_hash, is_without_splitting, decl, get_metadata


def get_toast_message(payload_ids):
    return (
        f"{decl(len(payload_ids), ['Создана', 'Созданы', 'Созданы'])} {decl(len(payload_ids), ['посылка', 'посылки', 'посылок'])} с "
        f"{decl(len(payload_ids), ['номером', 'номерами', 'номерами'])}: {', '.join(payload_ids)}"
    )


def send_payload(age, sex, files):
    if age is None:
        st.error("Введите возраст пациента")
        return

    if sex is None:
        st.error("Введите пол пациента")
        return

    if len(files) == 0:
        st.error("Прикрепите фотографии")
        return
    try:
        images = get_metadata(files)
    except ValueError:
        st.error("Одна и та же фотография прикреплена несколько раз")
        return

    duplicate = get_duplicate_name(images)

    if duplicate is not None:
        st.error(f"Изображение {duplicate} уже есть в базе данных")
        return

    payload_id = upload_images(
        patient_hash=get_patient_hash(
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), age
        ),
        sex="male" if sex == "Мужской" else "female",
        age=str(age),
        stage="before",
        case=3,
        hashes=[image_hash for image_hash in images.keys()],
        devices=[images[image_hash]["device"] for image_hash in images.keys()],
        files=[images[image_hash]["image"] for image_hash in images.keys()],
    )
    st.session_state.sent_payloads_ids.append(payload_id)
    st.session_state.toast_message = get_toast_message([payload_id])
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

if not is_without_splitting():
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

(files, contains_bad_photos) = file_uploader_segment("Фотографии")
total_photos = len(files)
button_label = f"Отправить ({total_photos} фото)"

if st.button(button_label):
    if contains_bad_photos:
        st.error("Посылка содержит битые файлы")
    else:
        send_payload(age=age, sex=sex, files=files)
