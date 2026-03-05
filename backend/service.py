import time
from collections import defaultdict

from backend.repo.payload import PayloadRepo
from backend.repo.image import ImageRepo
from backend.repo.patient import PatientRepo


def get_statistics(start: str, end: str):
    stats = {
        0: {},
        1: {},
        2: {},
        3: {},
        4: {}
    }

    cases = PatientRepo.get_case_stat(start, end)
    for case in cases:
        doctor = case[1]
        case_type = case[0]
        status = case[2]
        if doctor not in stats[case_type]:
            stats[case_type][doctor] = {
                "total": 0,
                "accepted": 0,
                "rejected": 0,
                "pending": 0,
            }

        stats[case_type][doctor]["total"] += 1
        stats[case_type][doctor][status] += 1

    return stats


def get_all_payloads_by_doctor_email(doctor, limit, page):
    """get doctor payloads / existing_payloads"""
    return PayloadRepo.all_payloads_by_doctor(doctor, limit, page)


def get_all_payloads(type: str):
    if type == "validation":
        resp = PayloadRepo.get_all_payloads_by_image_status("pending")
    elif type == "accepted":
        resp = PayloadRepo.get_all_payloads_by_image_status("accepted")
    elif type == "archive":
        resp = PayloadRepo.get_all_payloads_by_image_status("rejected")
    else:
        resp = PayloadRepo.get_all_payloads()
    r = defaultdict(dict)
    if resp is not None:
        for st in resp:
            if not r[st[0]]:
                r[st[0]] = {
                    "payload_stage": st[1],
                    "payload_case": st[2],
                    "status": st[3],
                    "patient": st[4],
                    "doctor": st[5],
                    "uploadtime": st[6],
                    "images": [(st[7], st[9], st[8])],
                    "case_id": st[10]
                }
            else:
                r[st[0]]["images"].append((st[7], st[9], st[8]))
    return r


def change_image_status(image_id: str, status: str, payload_id: int):
    ImageRepo.update_status(image_id, status)

    time.sleep(0.2)
    resp = PayloadRepo.get_images_statuses(payload_id)
    is_accepted = True
    case_id = resp[0][1]
    for row in resp:
        if row[0] == "accepted":
            pass
        elif row[0] == "rejected":
            print(f"changing status of payload {payload_id} and case to 'rejected'")
            PayloadRepo.update_status(payload_id, "rejected")
            case_id = PayloadRepo.get_case_id(payload_id)
            PatientRepo.update_status(case_id, "rejected")
            return "ok"
        else:
            is_accepted = False

    if is_accepted:
        print(f"changing status of payload {payload_id} to 'accepted'")
        PayloadRepo.update_status(payload_id, "accepted")

        if PatientRepo.check_case_accepted(case_id):
            PatientRepo.update_status(case_id, "accepted")
    return "ok"


def change_payload_status(payload_id: str, status: str):
    payload = PayloadRepo.update_status(payload_id, status)
    case_id = PayloadRepo.get_case_id(payload_id)

    if case_id:
        if status == "accepted":
            if PatientRepo.check_case_accepted(case_id):
                PatientRepo.update_status(case_id, "accepted")
        elif status == "rejected":
            PatientRepo.update_status(case_id, "rejected")
        elif status == "edited":
            PatientRepo.update_status(case_id, "pending")
    return "ok" if payload else None


def get_images_by_status(status: str):
    return ImageRepo.get_many_by_status(status)


def get_comment_by_id(id):
    """??"""
    resp = ImageRepo.get_comment(id)
    if resp is None:
        return None
    return resp[0]


def set_comment_by_id(id, comment):
    ImageRepo.update_comment(id, comment)
    return "ok"


def check_hash_duplicate(hash: str):
    resp = ImageRepo.get_count_by_hash(hash)
    return resp


def get_payload_by_id(id):
    return PayloadRepo.get_one(id)


def get_count_all_payloads(doctor_email):
    return PayloadRepo.count_all_payloads_by_doctor_email(doctor_email)


def get_payloads_by_caseid(case_id):
    return PayloadRepo.get_payloads_by_case_id(case_id)
