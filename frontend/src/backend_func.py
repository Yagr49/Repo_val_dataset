from io import BytesIO
from typing import List, Literal
import logging
from backend.db_service import send_data_to_db, send_files_to_s3, send_image_data_to_db
from backend.service import (
    change_image_status,
    change_payload_status,
    check_hash_duplicate,
    get_all_payloads,
    get_all_payloads_by_doctor_email,
    get_comment_by_id,
    get_payload_by_id,
    get_statistics,
    set_comment_by_id,
    get_count_all_payloads,
    get_payloads_by_caseid,
)
import boto3
import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from schemas.backend import Payload, Patient, PayloadImage
from config import Config

from utils import (
    datetime_to_string,
    decode_token,
    is_image_status_in_archive,
    is_image_status_on_verification,
    get_patient_hash,
    is_image_status_accepted,
    send_notification_to_doctor,
)

logger = logging.getLogger(__file__)
logger.setLevel(level=logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[{asctime}][{levelname:^8s}] ({filename}:{lineno}) ({funcName})): {message}",
    style="{",
)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.info("Starting frontend")

payload_statuses = {
    "accepted": "accepted",
    "pending": "pending",
    "edited": "edited",
    "rejected": "rejected",
}

payload_stages = {
    "before": "До гигиены",
    "coloring": "После окрашивания налёта",
    "after": "После гигиены",
    "other": "Фотографии с разного ракурса"
}


mapping_group_payload = {
    0: 'Группа 0 -  7 лет',
    1: 'Группа 1 - До 7 лет',
    2: 'Группа 2 - От 7 лет',
    3: 'Группа 3',
    4: 'Группа 4'
}


class Image:
    id: str
    status: str
    s3_url: str
    bytes: BytesIO

    def __init__(self, image_id, status, s3_path):
        self.id = image_id
        self.status = status
        if Config.DEV_MODE:
            self.s3_url = f"{Config.MINIO_URL}/{s3_path}"
            res = requests.get(self.s3_url)
            self.bytes = BytesIO(res.content)
        else:
            session = boto3.session.Session(
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            )
            s3_client = session.client(
                service_name="s3", endpoint_url=Config.AWS_ENDPOINT_URL
            )
            try:
                response = s3_client.get_object(
                    Bucket=Config.S3_BUCKET,
                    Key="/".join(s3_path.split("/")[1:]),
                    SSECustomerKey=Config.SSE_CUSTOM_KEY,
                    SSECustomerAlgorithm=Config.SSE_CUSTOM_ALGORITHM,
                )
                self.bytes = BytesIO(response["Body"].read())
            except Exception as e:
                self.bytes = "Невозможно отобразить фотографию"
                logger.info(e)


def get_all_payloads_st(type: str = "all"):
    res = get_all_payloads(type)
    response = []

    for key in sorted(res.keys(), reverse=True):
        images = []
        for image in res[key]["images"]:
            images.append(
                {
                    "id": image[1],
                    "status": image[2],
                    "s3_url": image[0],
                }
            )
        res[key]["id"] = key
        res[key]["images"] = images
        res[key]["pages"] = []
        if (
                len(
                    [
                        image
                        for image in images
                        if is_image_status_in_archive(image["status"])
                    ]
                )
                > 0
        ):
            res[key]["pages"].append("archive")
        if (
                len(
                    [
                        image
                        for image in images
                        if is_image_status_on_verification(image["status"])
                    ]
                )
                > 0
        ):
            res[key]["pages"].append("valid")
        if (
                len(
                    [image for image in images if is_image_status_accepted(image["status"])]
                )
                > 0
        ):
            res[key]["pages"].append("accepted")
        response.append(res[key])
    # logger.info(f"{response}")
    return response


def get_stats(start, end):
    resp = get_statistics(start, end)
    logger.info(f"{resp}")

    result = []
    for group in resp.values():
        doctors = []
        for doctor in group.keys():
            doctors.append(
                {
                    "doctor": doctor,
                    "accepted": group[doctor]["accepted"],
                    "rejected": group[doctor]["rejected"],
                    "pending": group[doctor]["pending"],
                    "total": group[doctor]["total"],
                }
            )

        result.append(doctors)
    return result


def fetch_images(images, filter_by_status):
    data = [item for item in images if item["status"] in filter_by_status]
    return [Image(*image.values()) for image in data]


def restore_image(image_id: str, image_status: str, payload_id: int):
    change_image_status(
        image_id, "pending" if image_status == "rejected" else "pending", payload_id
    )


def accept_image(image_id: str, image_status: str, payload_id: int):
    change_image_status(
        image_id, "accepted" if image_status == "pending" else "accepted", payload_id
    )


def reject_image(image_id: str, image_status: str, payload_id: int):
    change_image_status(
        image_id, "rejected" if image_status == "pending" else "rejected", payload_id
    )


def edited_image(image_id: str, image_status: str, payload_id: int):
    change_image_status(
        image_id, "edited" if image_status == "rejected" else "edited", payload_id
    )


def get_payloads(limit=3, page=2):
    try:
        user_info = st.session_state.get("user_info")
        doctor_email = user_info.email
        payloads = get_all_payloads_by_doctor_email(doctor_email, limit, page)
        logger.error(f"--------------{payloads}-----------------")
        return [
            {
                "id": payloads[i][0],
                "amount": payloads[i][3],
                "time": datetime_to_string(payloads[i][2]),
                "status": payload_statuses[payloads[i][1]],
            }
            for i in range(len(payloads) - 1, -1, -1)
        ]
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return []


def get_payload(payload_id):
    results = get_payload_by_id(payload_id)

    if results is None:
        return None

    try:
        image = results[0]
    except Exception as e:
        logger.info(e)
        return None

    images = []

    for image in results:
        images.append(Image(image_id=image[0], status=image[1], s3_path=image[2]))

    return {
        "id": payload_id,
        "doctor": image[3],
        "patient": image[5],
        "age": image[6],
        "sex": image[7],
        "payload_stage": image[8],
        "payload_case": image[9],
        "status": image[10],
        "uploadtime": image[4],
        "case_id": image[11],
        "images": images,
    }


def change_payload_status_st(payload_id, status):
    if status == "failed":
        try:
            user_info = st.session_state.user_info
            send_notification_to_doctor(user_info.email, payload_id)
        except Exception as e:
            logger.error(e)
    resp = change_payload_status(payload_id, status)
    return resp


def does_image_exist_in_db(image_hash: str):
    resp = check_hash_duplicate(image_hash)
    return resp == 1


def get_duplicate_name(images):
    duplicate = None
    for image_hash in images.keys():
        if does_image_exist_in_db(image_hash):
            duplicate = images[image_hash]["image"].name
            break
    return duplicate


def upload_images_for_stage(
        stage, images, patient_id, age, sex: Literal["male", "female"]
):
    if len(images) > 0:
        payload_id = upload_images(
            patient_hash=get_patient_hash(patient_id, age),
            sex=sex,
            age=str(age),
            stage=stage,
            case=1 if age < 7 else 2 if age > 7 else 0,
            hashes=[image_hash for image_hash in images.keys()],
            devices=[images[image_hash]["device"] for image_hash in images.keys()],
            files=[images[image_hash]["image"] for image_hash in images.keys()],
        )
        return payload_id
    return None


def create_payload_divided_stage(
        patient_id, age, sex, images_before, images_coloring, images_after, images_other
):
    uploaded_ids = []

    before_id = upload_images_for_stage("before", images_before, patient_id, age, sex)
    if before_id:
        uploaded_ids.append(before_id)

    coloring_id = upload_images_for_stage(
        "coloring", images_coloring, patient_id, age, sex
    )
    if coloring_id:
        uploaded_ids.append(coloring_id)

    after_id = upload_images_for_stage("after", images_after, patient_id, age, sex)
    if after_id:
        uploaded_ids.append(after_id)

    other_id = upload_images_for_stage("other", images_other, patient_id, age, sex)
    if other_id:
        uploaded_ids.append(other_id)

    return uploaded_ids


def set_comment(image_hash, comment):
    resp = set_comment_by_id(image_hash, comment)
    return resp


def get_comment(image_hash):
    resp = get_comment_by_id(image_hash)
    return resp


def get_payloads_case_id(case_id):
    try:
        payloads = get_payloads_by_caseid(case_id)
        return [
            {
                "id": payloads[i][0],
                "payload_case": payloads[i][6],
                "payload_stage": payloads[i][2],
                "time": datetime_to_string(payloads[i][5]),
                "doctor": payloads[i][4],
                "status": payloads[i][3],
                "images_count": payloads[i][7],
            }
            for i in range(len(payloads) - 1, -1, -1)
        ]
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return []


def send_payload(files: List[UploadedFile], payload: Payload):
    user_info = st.session_state.get("user_info")

    if user_info is None:
        raise "header authorization parameter is empty"

    payload.doctor = user_info.email

    #     with open(
    #         f"{tmp_base_dir}/{save_path}", "wb"
    #     ) as out_file:
    #         content = file.getbuffer()
    #         is_invalid = check_image_blur(content)
    #         file.seek(0)
    #         logger.debug(
    #             f"========================================is invalid {is_invalid}==================================="
    #         )

    #         img.status = "pending"

    payload = send_data_to_db(payload)
    paths = send_files_to_s3(files, payload)
    send_image_data_to_db(payload, paths)

    payload_id = payload.id

    return payload_id


def upload_images(
        patient_hash: str,
        sex: Literal["male", "female"],
        age: str,
        stage: str,
        case: int,
        hashes: List[str],
        devices: List[str],
        files: List[UploadedFile],
):
    images_obj = []
    for i in range(len(hashes)):
        filename = f"{hashes[i]}/{files[i].name.split('.')[-1]}"
        images_obj.append(
            PayloadImage(id=hashes[i], device=devices[i], filename=filename)
        )

    payload = Payload(
        payload_stage=stage,
        payload_case=case,
        patient=Patient(hash=patient_hash, age=age, sex=sex),
        images=images_obj,
        doctor=decode_token(st.session_state.keycloak.access_token)["sub"],
    )
    logger.info(f"{payload}")

    payload_id = send_payload(files=files, payload=payload)

    logger.info(f"{payload_id}")

    return str(payload_id)


def get_payloads_count():
    user_info = st.session_state.get("user_info")
    doctor_email = user_info.email
    logger.info(f"Count payloads for {doctor_email}")
    count_payloads = get_count_all_payloads(doctor_email)
    logger.error(count_payloads)
    return count_payloads
