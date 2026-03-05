from datetime import timedelta
from backend.repo.base import BaseRepo


class PatientRepo(BaseRepo):
    @classmethod
    def is_exists(cls, id: str):
        res = cls.execute_query("SELECT * FROM patient WHERE id=%s", (id,))
        return len(res) != 0

    @classmethod
    def get_case_id_by_hash(cls, patient_hash):
        query = """SELECT id FROM "case" WHERE patient_id = %s;"""
        return cls.execute_query(query, (patient_hash,), fetchone=True)[0]

    @classmethod
    def create_patient(cls, patient_hash, age, sex):
        query = "INSERT INTO patient (id, age, sex) VALUES (%s, %s, %s)"
        cls.execute_write_query(query, (patient_hash, age, sex))

    @classmethod
    def create_case(cls, patient_hash, case_type):
        query = """
                INSERT INTO "case" (patient_id, type, status)
                VALUES (%s, %s, %s) RETURNING id
                """
        case_status = "accepted" if case_type == 4 else "pending"
        case = cls.execute_query(
            query, (patient_hash, case_type, case_status), fetchone=True
        )
        return case[0]

    @classmethod
    def get_case_type(cls, case_id):
        query = """SELECT type FROM "case" WHERE id = %s;"""
        return cls.execute_query(query, (case_id,), fetchone=True)[0]

    @classmethod
    def get_case_stat(cls, start: str, end: str):
        end_date = end + timedelta(days=1)

        query = """
                SELECT DISTINCT
                    "case".type,
                    payload.doctor_email,
                    "case".status,
                    "case".id AS case_id,
                    "case".patient_id
                FROM
                    public."case"
                INNER JOIN (
                    SELECT
                        payload.case_id,
                        MIN(payload.upload_time) AS first_upload_time
                    FROM
                        payload
                    GROUP BY
                        payload.case_id
                    HAVING
                        MIN(payload.upload_time) >= %s
                        AND MIN(payload.upload_time) < %s
                ) AS first_payloads
                ON first_payloads.case_id = "case".id
                INNER JOIN
                    payload
                ON payload.case_id = first_payloads.case_id
                AND payload.upload_time = first_payloads.first_upload_time
                ORDER BY
                    "case".id;
                """
        return cls.execute_query(query=query, values=(start, end_date))

    @classmethod
    def get_not_sent_cases(cls):
        query = """
                SELECT id FROM "case"
                WHERE status = 'accepted' AND type IN (0, 1, 2, 4) AND sent_to_cvat_at IS NULL;
                """
        return cls.execute_query(query)

    @classmethod
    def get_not_sent_cases_type_3(cls):
        query = """
                SELECT id FROM "case"
                WHERE status = 'accepted' AND type = 3 AND sent_to_cvat_at IS NULL;
                """
        return cls.execute_query(query)

    @classmethod
    def update_many_case_sent_flag(cls, cases_ids: list[int]):
        query = """
            UPDATE "case"
            SET sent_to_cvat_at = NOW()
            WHERE id = ANY(%s)
        """
        cls.execute_write_query(query, (cases_ids,))

    @classmethod
    def check_case_accepted(cls, case_id):
        query = """
                SELECT "case".id
                FROM "case"
                         INNER JOIN payload ON payload.case_id = "case".id
                WHERE "case".id = %s \
                  AND (
                    (
                        EXISTS (SELECT 1 \
                                FROM payload \
                                WHERE status = 'accepted' AND stage = 'before' AND case_id = "case".id) AND
                        EXISTS (SELECT 1 \
                                FROM payload \
                                WHERE status = 'accepted' AND stage = 'after' AND case_id = "case".id) AND
                        EXISTS (SELECT 1 \
                                FROM payload \
                                WHERE status = 'accepted' AND stage = 'coloring' AND case_id = "case".id)
                        ) OR (
                        "case".type = 3 AND
                        EXISTS (SELECT 1 FROM payload WHERE status = 'accepted' AND case_id = "case".id)
                        )
                    );
                """
        return cls.execute_query(query, (case_id,), fetchone=True)

    @classmethod
    def update_status(cls, case_id: int, status: str):
        query = """UPDATE "case" SET status = %s WHERE id = %s"""
        return cls.execute_write_query(query, (status, case_id))
