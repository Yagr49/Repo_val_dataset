import base64
import hashlib
import json
import datetime
from io import BytesIO

import jwt
import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS

from config import Config
from schemas.backend import User

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import numpy as np
import io
import cv2

months = {
    "January": "Января",
    "February": "Февраля",
    "March": "Марта",
    "April": "Апреля",
    "May": "Мая",
    "June": "Июня",
    "July": "Июля",
    "August": "Августа",
    "September": "Сентября",
    "October": "Октября",
    "November": "Ноября",
    "December": "Декабря",
}


def check_image_blur(image_bytes: bytes) -> bool:
    """The function of determining the degree of blurring of the image

    Parameters
    ----------
    image_bytes : bytes
        String of bytes

    Returns
    -------
    bool
        True - if the degree of blurring is above the threshold
        False - if the degree of blurring is below the threshold
    """

    image = Image.open(io.BytesIO(image_bytes))
    image = np.array(image.convert("L"))
    laplacian = cv2.Laplacian(image, cv2.CV_64F)
    variance = laplacian.var()

    return variance > 11.73


def datetime_to_string(date_to_convert):
    if isinstance(date_to_convert, datetime.datetime):
        dt = date_to_convert
    else:
        dt = datetime.strptime(date_to_convert, "%Y-%m-%dT%H:%M:%S%z")
    formatted = dt.strftime("%d %B %Y %H:%M")
    for end in months:
        formatted = formatted.replace(end, months[end])
    return formatted


def date_to_string(date_to_convert):
    dt = datetime.strptime(date_to_convert, "%d-%m-%Y")
    formatted = dt.strftime("%d %B %Y")
    for end in months:
        formatted = formatted.replace(end, months[end])
    return formatted


def get_image_bytes(img):
    file = BytesIO(img.getvalue())
    file.name = img.name
    return file


def decode_token(encoded_token):
    payload_part = encoded_token.split(".")[1]
    payload_part += "=" * (-len(payload_part) % 4)
    decoded_bytes = base64.urlsafe_b64decode(payload_part)
    payload = json.loads(decoded_bytes)
    return payload


def get_roles(access_token):
    payload = decode_token(access_token)
    return payload["realm_access"]["roles"]


def is_divided_into_stages():
    if "keycloak_roles" not in st.session_state:
        return False
    return Config.KEYCLOAK_DIVIDED_STAGES_ROLE in st.session_state.keycloak_roles


def is_without_splitting():
    if "keycloak_roles" not in st.session_state:
        return False
    return Config.KEYCLOAK_WITHOUT_SPLITTING_ROLE in st.session_state.keycloak_roles


def is_admin():
    if "keycloak_roles" not in st.session_state:
        return False
    return Config.KEYCLOAK_ADMIN_ROLE in st.session_state.keycloak_roles


def get_patient_hash(full_name: str, age: int, add_timestamp: bool = False):
    patient_id = full_name.replace(" ", "").replace("ё", "е").lower() + str(age)
    if add_timestamp:
        patient_id += datetime.now().strftime("/%Y-%m-%d-%H-%M-%S")
    return hashlib.md5(patient_id.encode("utf-8")).hexdigest()


def get_age_from_birth_date(born: datetime.date):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def decl(number: int, titles: list):
    cases = [2, 0, 1, 1, 1, 2]
    if 4 < number % 100 < 20:
        idx = 2
    elif number % 10 < 5:
        idx = cases[number % 10]
    else:
        idx = cases[5]

    return titles[idx]


def is_image_status_in_archive(status):
    return status in ["rejected"]


def is_image_status_on_verification(status):
    return status in ["pending"]


def is_image_status_automatic_validation_failed(status):
    return status in [2, 4, 5]


def is_image_status_accepted(status):
    return status in ["accepted"]


def get_payload_case(payload_clinic, payload_patient_dob):
    age = get_age_from_birth_date(payload_patient_dob)

    case = (
        4
        if payload_clinic is None
        else (3 if payload_clinic == 2 else (0 if age == 7 else (1 if age < 7 else 2)))
    )

    return case


def get_device(file):
    try:
        image = Image.open(file)
    except Exception as e:
        print(e)
        return ""

    exif_data = image.getexif()

    device = ""

    for tag_id in exif_data:
        tag = TAGS.get(tag_id, tag_id)
        if tag == "Make" or tag == "Model":
            data = exif_data.get(tag_id)
            if isinstance(data, bytes):
                data = data.decode()

            print(file, tag, data)
            if device == "":
                device = data
            else:
                device += f"-{data}"

    return "undefined" if device == "" else device


def get_user_info(token) -> User:
    token_decode = jwt.decode(
        token,
        key=f"-----BEGIN PUBLIC KEY-----{Config.keycloak_openid.public_key()}-----END PUBLIC KEY-----",
        algorithms=["RS256"],
        options={"verify_aud": False, "verify_signature": True},
    )

    payload = token_decode
    return User(
        id=payload.get("sub"),
        username=payload.get("preferred_username"),
        email=payload.get("email"),
        realm_roles=payload.get("realm_access", {}).get("roles", []),
        client_roles=payload.get("resource_access", {})
        .get(Config.KEYCLOAK_FRONTEND_CLIENT or "", {})
        .get("roles", []),
    )


def send_notification_to_doctor(doctor, id):
    if not Config.SEND_ADDRESS or not Config.PASSWORD:
        return {"resp": "Email not configured"}
    msg = MIMEMultipart()
    msg["Subject"] = "Уведомление MedForce"
    msg["From"] = Config.SEND_ADDRESS
    msg["To"] = doctor
    base_url = (Config.APP_BASE_URL or "").rstrip("/")
    msg.attach(
        MIMEText(
            f"Здравствуйте! Ваша посылка №{id} содержит размытые фотографии.\n\n{base_url}/",
            "html",
        )
    )
    try:
        smtp = smtplib.SMTP_SSL("smtp.yandex.ru", 465)
        smtp.login(Config.SEND_ADDRESS, Config.PASSWORD)
        smtp.send_message(msg)
        return {"resp": "Email sent"}
    except smtplib.SMTPException as e:
        raise e


def get_metadata(files):
    data = {}

    for file in files:
        image_hash = hashlib.md5(file.read()).hexdigest()
        image_bytes = get_image_bytes(file)
        device = get_device(image_bytes)
        if image_hash in data:
            raise ValueError(f"Duplicate image hash: {image_hash}")
        data[image_hash] = {"device": device, "image": file, "bytes": image_bytes}

    return data
