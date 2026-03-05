import streamlit as st
from streamlit_theme import st_theme
from streamlit_js_eval import get_page_location

from components.localization import localization
from components.authenticate import authenticate

from backend_func import (
    get_payload,
    change_payload_status_st,
    get_duplicate_name,
    payload_statuses,
    payload_stages,
    get_comment,
    set_comment,
    upload_images,
    edited_image,
)
from components.page_config import page_config
from components.photo_display import photo_display
from components.sidebar import sidebar
from config import Config
from utils import (
    decl,
    is_divided_into_stages,
    is_without_splitting,
    is_admin,
    decode_token,
    datetime_to_string,
    is_image_status_in_archive,
    get_metadata
)


# Title and favicon
page_config("Редактирование")

# Translation
localization()


# Authentication and authorization
authenticate()

if "keycloak_roles" not in st.session_state:
    st.stop()

if not (is_divided_into_stages() or is_without_splitting()) or "id" not in st.query_params:
    st.switch_page("main.py")

if 'is_diag_opened' in st.session_state:
    st.session_state['is_diag_opened'] = False

# State init
payload_id = st.query_params.id

if "edit_payload" not in st.session_state:
    st.session_state.edit_payload = get_payload(payload_id)

if (
    "contains_bad_photos" not in st.session_state
    or st.session_state.contains_bad_photos
):
    st.session_state.contains_bad_photos = False


# Sidebar
if st.sidebar.button("Создать новую посылку"):
    if is_admin():
        st.switch_page("pages/upload_admin.py")
    if is_divided_into_stages():
        st.switch_page("pages/upload.py")
    if is_without_splitting():
        st.switch_page("pages/upload_clinic2.py")
theme = st_theme()
location = get_page_location()
sidebar(
    location=location,
    theme=theme,
    display_nav=True,
    display_logout=True,
    display_payloads=True,
)


# Page
payload = st.session_state.edit_payload

user_data = decode_token(st.session_state.keycloak.access_token)

if (
    payload is None
    or payload["doctor"] != user_data["email"]
    or payload_statuses[payload["status"]] != "rejected"
):
    st.switch_page("main.py")

st.header(f"Посылка №{payload['id']} не прошла ручную поверку")

st.write("Просим вас по возможности переснять и дозагрузить фотографии")

st.subheader("Информация о пациенте:")

st.write(
    f"Возраст: {payload['age']} {decl(int(payload['age']), ['год', 'года', 'лет'])}"
)
st.write(f"Пол: {'Мужской' if payload['sex'] == 'male' else 'Женский'}")
st.write(f"Состояние: {payload_stages[payload['payload_stage']]}")
st.write(f"Посылка загружена: {datetime_to_string(payload['uploadtime'])}")

files = st.file_uploader(
    "Дозагрузка фотографий:",
    accept_multiple_files=True,
    type=Config.FRONTEND_FILE_ACCEPT.split(","),
)

photos = []
comments = []
ids = []
status = []
for image in payload["images"]:
    if not is_image_status_in_archive(image.status):
        continue
    comment = get_comment(image.id)
    if comment is None or comment == "":
        continue
    photos.append(image.bytes)
    comments.append(comment)
    ids.append(image.id)
    status.append(image.status)

if len(photos) == 0:
    st.switch_page("main.py")

if len(files) != 0:
    st.subheader("Дозагруженные фотографии")
    st.session_state.contains_bad_photos = photo_display(files)

    payload_clinic = None

    if payload["payload_case"] == 1 or payload["payload_case"] == 2 or payload["payload_case"] == 0:
        payload_clinic = 1
    if payload["payload_case"] == 3:
        payload_clinic = 2

    if st.button("Отправить"):
        try:
            images = get_metadata(files)
            duplicate = get_duplicate_name(images)

            if st.session_state.contains_bad_photos:
                st.error("Прикреплённые фотографии содержат битые файлы")
            elif duplicate is not None:
                st.error(f"Изображение {duplicate} уже есть в базе данных")
            else:
                upload_images(
                    patient_hash=payload["patient"],
                    sex=payload["sex"],
                    age=payload["age"],
                    stage=payload["payload_stage"],
                    case=payload["payload_case"],
                    hashes=[image_hash for image_hash in images.keys()],
                    devices=[
                        images[image_hash]["device"] for image_hash in images.keys()
                    ],
                    files=[images[image_hash]["image"] for image_hash in images.keys()],
                )
                change_payload_status_st(payload_id, "edited")
                for rej_img in range(len(ids)):
                    edited_image(ids[rej_img], status[rej_img], payload_id)
                for photo_id in ids:
                    set_comment(photo_id, None)
                st.switch_page("main.py")
        except ValueError:
            st.error("Одна и та же фотография прикреплена несколько раз")

st.subheader("Размытые фотографии в посылке")

photo_display(photos, dynamic_columns=False, comments=comments)
