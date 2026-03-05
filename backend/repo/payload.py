from backend.repo.base import BaseRepo


class PayloadRepo(BaseRepo):
    @classmethod
    def get_one(cls, pid):
        query = """SELECT image.id, image.status, s3_path, payload.doctor_email,
                 payload.upload_time, patient.id, patient.age, patient.sex,
                 payload.stage, "case".type, payload.status, payload.case_id
                 FROM image
                 INNER JOIN payload ON image.payload_id = payload.id
                 INNER JOIN "case" ON "case".id = payload.case_id
                 INNER JOIN patient ON "case".patient_id = patient.id
                 WHERE image.payload_id=%s;"""
        return cls.execute_query(query, (pid,))

    @classmethod
    def create(cls, case_id, stage, status, doctor_email, up_time):
        query = (
            "INSERT INTO payload (case_id, stage, status, doctor_email, upload_time) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id"
        )
        # logging.info(F"Payload №{created_id[0]} was created successfully")
        return cls.execute_query(
            query, (case_id, stage, status, doctor_email, up_time), fetchone=True
        )[0]

    @classmethod
    def update_status(cls, payload_id: int, status: str):
        query = "UPDATE payload SET status = %s WHERE id = %s"
        return cls.execute_write_query(query, (status, payload_id))

    @classmethod
    def all_payloads_by_doctor(cls, doctor, limit, page):
        query = """SELECT payload.id, payload.status, payload.upload_time, count(image.payload_id)
        FROM payload
        INNER JOIN image on payload.id = image.payload_id and doctor_email=%s
        group by payload.id ORDER BY payload.id DESC LIMIT %s OFFSET %s
        """
        ans = cls.execute_query(
            query,
            (
                doctor,
                limit,
                (page - 1) * limit,
            ),
        )
        return ans

    @classmethod
    def get_all_payloads(cls, limit: int = 100):
        query = """SELECT payload.id, payload.stage, "case".type, payload.status,
                "case".patient_id, payload.doctor_email, payload.upload_time,
                image.s3_path, image.status, image.id, payload.case_id
                FROM payload
                right JOIN image on payload.id = image.payload_id
                LEFT JOIN "case" on "case".id = payload.case_id
                group by payload.id, image.s3_path, image.status, image.id, "case".type, "case".patient_id
                ORDER BY payload.id
                LIMIT %s"""
        resp = cls.execute_query(query, (limit,))
        return resp

    @classmethod
    def get_all_payloads_by_image_status(cls, img_status: str):
        query = """SELECT payload.id, payload.stage, "case".type, payload.status,
                    "case".patient_id, payload.doctor_email, payload.upload_time,
                    image.s3_path, image.status, image.id, payload.case_id
                    FROM payload
                    right JOIN image on payload.id = image.payload_id
                    LEFT JOIN "case" on "case".id = payload.case_id
                    WHERE image.status = %s
                    group by payload.id, image.s3_path, image.status, image.id, "case".type, "case".patient_id
                    ORDER BY payload.id"""
        resp = cls.execute_query(
            query,
            (img_status,),
        )
        return resp

    @classmethod
    def get_images_statuses(cls, pid):
        query = """SELECT image.status, payload.case_id
                 from payload
                 inner join image on image.payload_id = payload.id
                 and payload.id = %s;"""
        return cls.execute_query(query, (pid,))

    @classmethod
    def get_case_id(cls, pid):
        query = """SELECT case_id FROM payload WHERE id = %s;"""
        ans = cls.execute_query(query, (pid,), fetchone=True)
        return ans[0] if ans else None

    @classmethod
    def count_all_payloads_by_doctor_email(cls, doctor: str):
        query = """SELECT payload.id, payload.status, payload.upload_time, count(image.payload_id)
                FROM payload
                INNER JOIN image on payload.id = image.payload_id and payload.doctor_email=%s group by payload.id
                ORDER BY payload.id"""
        ans = cls.execute_query(query, (doctor,))
        return len(ans)

    @classmethod
    def get_payloads_by_case_id(cls, case_id: int):
        query = """
                SELECT
                    p.*,
                    c.type AS case_type,
                    COUNT(i.id) AS image_count
                FROM payload p
                LEFT JOIN image i ON p.id = i.payload_id
                JOIN "case" c ON p.case_id = c.id
                WHERE p.case_id = %s
                GROUP BY p.id, c.type;
                """
        return cls.execute_query(query, (case_id,))
