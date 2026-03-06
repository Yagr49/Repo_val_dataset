import datetime
import glob
import logging
import os
import shutil
import uuid

import PIL

from backend.repo.patient import PatientRepo
from backend.repo.payload import PayloadRepo
from backend.repo.image import ImageRepo

from s3_adapters.yandex_adapter import YandexAdapter
from cvat_adapter.cvat_adapter import CVATAdapter

logger = logging.getLogger(__file__)
logger.setLevel(level=logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[{asctime}][{levelname:^8s}] ({filename}:{lineno}) ({funcName})): {message}",
    style="{",
)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

client = YandexAdapter(logger=logger)

cvat_host = os.environ.get("CVAT_HOST")
cvat_user = os.environ.get("CVAT_USER")
cvat_password = os.environ.get("CVAT_PASSWORD")

c_adapter = CVATAdapter(cvat_host, cvat_user, cvat_password, logger)


def send_files_to_s3(files, payload):
    logger.info(f"PAYLOAD ID IS {payload.id}")
    s3_paths = []
    for file, img in zip(files, payload.images):
        logger.info(f"export to s3 {file}")
        ext = file.name.split(".")[-1]
        img.s3_path = f"{payload.patient.hash}/{img.id}.{ext}"
        content = file.getvalue()
        client.upload(content, img.s3_path, os.environ["S3_BUCKET"])
        s3_paths.append(img.s3_path)
    return s3_paths


def send_image_data_to_db(payload, paths):
    imagesdata = []
    images_statuses = []
    payload_id = payload.id
    case = payload.payload_case
    for image, path in zip(payload.images, paths):

        image.s3_path = f'{os.environ["S3_BUCKET"]}/{path}'
        images_statuses.append(image.status if case != 4 else 'accepted')

        try:
            id = uuid.UUID(image.id)
        except ValueError:
            raise Exception("Невалидный UUID")

        if not ImageRepo.is_exists(str(id)):
            imagesdata.append(
                (str(id), payload_id, image.status if case != 4 else 'accepted', image.s3_path, image.device)
            )
        else:
            logger.info("This image is already exists")

    logger.debug(images_statuses)

    ImageRepo.create_many(images_data=imagesdata)
    return "ok"


def send_data_to_db(payload):
    offset = datetime.timedelta(hours=3)
    tz = datetime.timezone(offset, name="МСК")
    ft = "%Y-%m-%dT%H:%M:%S%z"
    t = datetime.datetime.now(tz=tz).strftime(ft)

    payload.uploadtime = t

    if not PatientRepo.is_exists(payload.patient.hash):
        PatientRepo.create_patient(
            patient_hash=payload.patient.hash,
            age=payload.patient.age,
            sex=payload.patient.sex,
        )
        case_id = PatientRepo.create_case(
            patient_hash=payload.patient.hash, case_type=payload.payload_case
        )
    else:
        case_id = PatientRepo.get_case_id_by_hash(payload.patient.hash)

    payload_id = PayloadRepo.create(
        case_id=case_id,
        stage=payload.payload_stage,
        status="pending" if payload.payload_case != 4 else 'accepted',
        doctor_email=payload.doctor,
        up_time=payload.uploadtime,
    )

    payload.id = payload_id

    return payload


def send_cvat_tag(cases, num_of_pats=20, task_name="Tagging"):
    if len(cases) < num_of_pats:
        return
    all_cases = [case[0] for case in cases]
    PatientRepo.update_many_case_sent_flag(all_cases)
    allimgs = ImageRepo.get_before_paths_by_case_ids_list(all_cases)
    logger.info(f"count of images of {num_of_pats} patients = {len(allimgs)}")

    all_paths = []
    logger.info(allimgs)
    for im in allimgs:
        all_paths.append(im[0])

    for path in all_paths:
        os.makedirs(
            f"/app/tmp_files/cvat_prep/{path.split('/')[-2]}/", exist_ok=True
        )

        client.download_to_file(
            path,
            f"/app/tmp_files/cvat_prep/{path.split('/')[-2]}/{path.split('/')[-1]}",
        )
    patient_folders = glob.glob("/app/tmp_files/cvat_prep/*")
    _decimate_low_res(patient_folders)
    c_adapter.create_tagging_task(
        _calculate_assignee_id(), "/app/tmp_files/cvat_prep_bestres", task_name
    )
    shutil.rmtree("/app/tmp_files/cvat_prep")


def export_cvat():
    tasks = c_adapter.get_tasks()
    for task in tasks:
        if task.status == "completed" and task.project_id == 2:
            imges = c_adapter.get_image_names(task.id)
            for image in imges:
                img_id = image.split(".")[0]
                logger.warning(img_id)
                payload_id = ImageRepo.get_payload_id(img_id)[0]
                logger.warning(payload_id)

                case_id = PayloadRepo.get_case_id(payload_id)
                logger.warning(case_id)

                case_type = PatientRepo.get_case_type(case_id)
                logger.warning(case_type)
                path = c_adapter.export_dataset(task.id)

                with open(path, "rb") as f:
                    client.upload(f.read(), path.rsplit("/", maxsplit=1)[-1], os.environ["EXPORT_S3_BUCKET"])
                os.remove(path)

                if case_type == 4:
                    continue

                s3_path = ImageRepo.get_path_by_id(img_id)
                patient_hash = s3_path.split("/")[1]
                os.makedirs("/app/tmp_files/cvat_prep/images/", exist_ok=True)
                os.makedirs(
                    f"/app/tmp_files/cvat_prep/images/{patient_hash}/", exist_ok=True
                )

                before_paths = ImageRepo.get_paths_by_patient_and_stage(
                    patient_hash, "before"
                )

                os.makedirs(
                    f"/app/tmp_files/cvat_prep/images/{patient_hash}/before",
                    exist_ok=True,
                )
                for path in before_paths:
                    client.download_to_file(
                        path[0],
                        f"/app/tmp_files/cvat_prep/images/{patient_hash}/before/{path[0].split('/')[-1]}",
                    )

                coloring_paths = ImageRepo.get_paths_by_patient_and_stage(
                    patient_hash, "coloring"
                )
                os.makedirs(
                    f"/app/tmp_files/cvat_prep/images/{patient_hash}/coloring",
                    exist_ok=True,
                )
                for path in coloring_paths:
                    client.download_to_file(
                        path[0],
                        f"/app/tmp_files/cvat_prep/images/{patient_hash}/coloring/{path[0].split('/')[-1]}",
                    )

            c_adapter.create_annotation_task(
                "/app/tmp_files/cvat_prep", task.id, _calculate_assignee_id()
            )
        elif task.status == "completed" and task.project_id in (1, 6):
            path = c_adapter.export_dataset(task.id, task.name)
            logger.warning(path)
            with open(path, "rb") as f:
                client.upload(f.read(), path.rsplit("/", maxsplit=1)[-1], os.environ["EXPORT_S3_BUCKET"])
            os.remove(path)
            with c_adapter.make_client() as cvat_client:
                cvat_client.tasks.remove_by_ids([task.id])


def _decimate_low_res(patient_folders):
    os.makedirs("/app/tmp_files/cvat_prep_bestres/", exist_ok=True)
    for folder in patient_folders:
        imgs = glob.glob(folder + "/*")
        max_pixels = 0
        maxres_path = ""
        for im in imgs:
            img = PIL.Image.open(im)
            wid, hgt = img.size
            pixels = wid * hgt  # Количество пикселей
            if pixels > max_pixels:
                max_pixels = pixels
                maxres_path = im
        if maxres_path:
            os.rename(
                maxres_path,
                f"/app/tmp_files/cvat_prep_bestres/{maxres_path.split('/')[-1]}",
            )


def _calculate_assignee_id():
    len_tasks = len(c_adapter.get_tasks())
    # todo почему так??????
    # return len_tasks % (len(c_adapter.get_users()) - 1) + 2
    return len_tasks % len(c_adapter.get_users()) + 1

# def chunks(lst, n):
#     """
#     Yield successive n-sized chunks from lst.
#     TODO: нужен ли?
#     """
#     for i in range(0, len(lst), n):
#         yield lst[i:i + n]
#
#
# def split_to_chunks(arr, vol):
#     """TODO: нужен ли?"""
#     arr_chunked = list(chunks(arr, vol))
#     if len(arr_chunked[-1]) == vol:
#         return arr_chunked
#     else:
#         arr_chunked[-2] = arr_chunked[-2] + arr_chunked[-1]
#         del arr_chunked[-1]
#         return arr_chunked
