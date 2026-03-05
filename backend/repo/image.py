from backend.repo.base import BaseRepo


class ImageRepo(BaseRepo):
    @classmethod
    def is_exists(cls, image_hash: str):
        res = cls.execute_query("SELECT * FROM image WHERE id=%s", (image_hash,))
        return len(res) != 0

    @classmethod
    def get_path_by_id(cls, img_id):
        return cls.execute_query(
            "SELECT s3_path FROM image  WHERE id = %s", (img_id,), fetchone=True
        )[0]

    @classmethod
    def get_count_by_hash(cls, hash):
        return cls.execute_query(
            "SELECT count(*) FROM image WHERE id = %s", (hash,), fetchone=True
        )[0]

    @classmethod
    def create_many(cls, images_data: list):
        """[(id, payload_id, status, s3_path, device_name),]"""
        query = """
                INSERT INTO image (id, payload_id, status, s3_path, device_name)
                VALUES (%s,%s,%s,%s,%s);
                """
        cls.execute_write_query(query=query, values=images_data, many=True)
        return "ok"

    @classmethod
    def get_payload_id(cls, img_id):
        query = "SELECT payload_id from image where id = %s"
        return cls.execute_query(query, (img_id,), fetchone=True)

    @classmethod
    def get_comment(cls, id):
        query = "SELECT comment from image where id=%s"
        return cls.execute_query(query, (id,), fetchone=True)

    @classmethod
    def update_comment(cls, id, comment):
        query = "UPDATE image SET comment = %s WHERE id = %s"
        return cls.execute_write_query(query, (comment, id))

    @classmethod
    def get_many_by_status(cls, status: str):
        return cls.execute_query("SELECT * from image where status=%s", (status,))

    @classmethod
    def update_status(cls, img_id: str, status: str):
        query = "UPDATE image SET status = %s WHERE id = %s"
        return cls.execute_write_query(query, (status, img_id))

    @classmethod
    def get_before_paths_by_case_ids_list(cls, case_list: list):
        query = """
                SELECT image.s3_path FROM payload
                INNER JOIN image ON image.payload_id = payload.id
                AND payload.stage = 'before'
                AND payload.case_id = ANY(%s);
                """
        return cls.execute_query(query, (case_list,))

    @classmethod
    def get_paths_by_patient_and_stage(cls, patient_hash, stage):
        query = """
                SELECT s3_path FROM image
                INNER JOIN payload ON image.payload_id = payload.id
                AND payload.stage = %s
                INNER JOIN "case" ON "case".id = payload.case_id
                AND "case".patient_id = %s
                """
        return cls.execute_query(query, (stage, patient_hash))
