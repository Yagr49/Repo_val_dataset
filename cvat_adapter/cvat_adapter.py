import glob
import json
import logging
import os
import shutil
import zipfile
from typing import List

from PIL import Image

import cvat_sdk
from cvat_sdk.core.proxies import users, tasks


class CVATAdapter:
    """
    This class serves as an adapter for interacting with the CVAT (Computer Vision Annotation Tool) API.
    """

    def __init__(
            self,
            host: str,
            user: str,
            password: str,
            logger: logging.Logger,
    ):
        """Initializes the CVATAdapter instance.

        Args:
            host (str): The hostname of the CVAT server.
            user (str): Username for authenticating to the CVAT server.
            password (str): Password for authenticating to the CVAT server.
            logger (logging.Logger): A logging.Logger instance for logging messages.
        """
        self.host = host
        self.user = user
        self.password = password
        self.logger = logger
        self.annotation_format = "Datumaro 1.0"

    @staticmethod
    def group_by_resolution(images_paths: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
        """Deletes all 'coloring' images except the one with the highest resolution
        from the provided list of image paths.

        Args:
            images_paths (list[str]): A list of file paths to the images.

        Returns:
            tuple[list[str], list[str]]: A tuple containing 4 lists:
                - The first list contains the path to the image with the highest resolution.
                - The second list contains paths to images that do not contain 'coloring' in their names.
        """

        before_images = []
        coloring_images = []

        for image_path in images_paths:
            with Image.open(image_path) as img:
                resolution = img.width * img.height
            # Классификация изображений
            if 'before' in image_path:
                before_images.append((resolution, image_path))
            elif 'coloring' in image_path:
                coloring_images.append((resolution, image_path))

        # Обработка категории 'before'
        max_before = []
        min_before = []
        if before_images:
            max_res = max(res for res, _ in before_images)
            for res, path in before_images:
                if res == max_res and not max_before:
                    max_before.append(path)  # Первое изображение с максимальным разрешением
                else:
                    min_before.append(path)

        # Обработка категории 'coloring'
        max_coloring = []
        min_coloring = []
        if coloring_images:
            max_res = max(res for res, _ in coloring_images)
            for res, path in coloring_images:
                if res == max_res and not max_coloring:
                    max_coloring.append(path)  # Первое изображение с максимальным разрешением
                else:
                    min_coloring.append(path)

        return max_before, max_coloring, min_before, min_coloring

    def make_client(self) -> cvat_sdk.Client:
        """Creates and returns a client to interact with the CVAT API.

        Returns:
            A CVAT client instance.
        """
        return cvat_sdk.make_client(
            host=self.host, credentials=(self.user, self.password)
        )

    def create_tagging_task(
            self,
            assignee_id: int,
            images_dir: str,
            task_name: str
    ):
        """Creates a tagging task in CVAT using the provided images and assigns it to an user.

        Args:
            assignee_id (int): The ID of the user to whom the task is assigned.
            images_dir (str): Directory containing images for the task. This directory
            will be deleted after the task creation.
        """
        task_spec = {
            "name": f"Task ({task_name})",
            "project_id": 2,
            "assignee_id": assignee_id,
            "labels": [],
        }
        with self.make_client() as client:
            client.tasks.create_from_data(
                spec=task_spec, resources=glob.glob(os.path.join(images_dir, "*"))
            )
        shutil.rmtree(images_dir)

    def get_image_names(self, task_id: int) -> List[str]:
        """Retrieves the names of images associated with a given CVAT task.

        Args:
            task_id (int): The ID of the CVAT task.

        Returns:
            A list of image names (strings).
        """
        with self.make_client() as client:
            return [
                meta["name"]
                for meta in client.tasks.retrieve(task_id).get_frames_info()
            ]

    def get_users(self) -> List[users.User]:
        """Retrieves a list of users from the CVAT server.

        Returns:
            A list of user objects.
        """
        with self.make_client() as client:
            return client.users.list()

    def get_tasks(self) -> List[tasks.Task]:
        """Retrieves a list of tasks from the CVAT server.

        Returns:
            A list of task objects.
        """
        with self.make_client() as client:
            return client.tasks.list()

    def export_dataset(self, task_id: int, task_name: str = "") -> str:
        """Exports the dataset for a given CVAT task.

        Args:
            task_id (int): The ID of the CVAT task.

        Returns:
            The path to the exported dataset file.
        """
        path = f"tmp_files/dataset-task-{task_id}{'-' + task_name if task_name else ''}.zip"
        if os.path.exists(path):
            os.remove(path)
        with self.make_client() as client:
            client.tasks.retrieve(task_id).export_dataset(
                format_name=self.annotation_format, filename=path
            )
        return path

    def move_task(self, task_id: int, dest_project_id: int) -> None:
        with self.make_client() as client:
            for id_ in [job['id'] for job in client.jobs.api.list(task_id=task_id)[0]["results"]]:
                client.jobs.retrieve(id_).update({'state': 'new', 'stage': 'annotation'})

            client.tasks.retrieve(task_id).update(
                {'project_id': dest_project_id, 'name': 'Task (Annotation, Type III)'})

    def _create_task(
            self,
            path: str,
            ann_json: dict,
            images_path: list[str],
            assignee_id: int,
            type: str,
            task_name: str,
            project_id
    ):
        """Helper method to create a task in CVAT.

        Args:
            path (str): Directory where dataset files are stored.
            ann_json (dict): JSON representation of the annotation.
            images_path (List[str]): List of image file paths.
            assignee_id (int): The ID of the user to whom the task will be assigned.
            type (str): Type of the task ('before' or 'coloring').
            task_name (str): Name of the task .
        """

        os.makedirs(os.path.join(path, type, "annotations"), exist_ok=True)

        with open(os.path.join(path, type, "annotations/default.json"), "w") as f:
            json.dump(ann_json, f, indent=2)

        shutil.make_archive(os.path.join(path, type), "zip", os.path.join(path, type))

        with self.make_client() as client:
            client.tasks.create_from_data(
                spec={
                    "name": task_name,
                    "project_id": project_id,
                    "assignee_id": assignee_id,
                },
                resources=images_path,
                annotation_path=os.path.join(path, f"{type}.zip"),
                annotation_format=self.annotation_format,
            )

    def create_annotation_task(self, path: str, task_id: int, assignee_id: int):
        """Creates an annotation task in CVAT using the provided images and annotations.

        Args:
            path: Directory where dataset files are stored.
            task_id: The ID of the original task to be processed.
            assignee_id: The ID of the user to whom the new tasks will be assigned.
        """

        task_type_suffix = ""

        with self.make_client() as client:
            if 'III' in client.tasks.retrieve(task_id).name:
                task_type_suffix = ", Type III"

        os.makedirs(path, exist_ok=True)

        if os.path.exists(os.path.join(path, "dataset.zip")):
            os.remove(os.path.join(path, "dataset.zip"))

        with self.make_client() as client:
            client.tasks.retrieve(task_id).export_dataset(
                filename=os.path.join(path, "dataset.zip"),
                format_name=self.annotation_format,
                include_images=False,
            )

        with zipfile.ZipFile(os.path.join(path, "dataset.zip"), "r") as zip_ref:
            zip_ref.extract(member="annotations/default.json", path=path)

        with open(os.path.join(path, "annotations/default.json"), "r") as ann_file:
            ann_json = json.load(ann_file)

        items = ann_json["items"].copy()
        ann_json["items"] = []
        annotations = {
            "max_before": ann_json.copy(),
            "max_coloring": ann_json.copy(),
            "min_before": ann_json.copy(),
            "min_coloring": ann_json.copy()
        }
        paths = {
            "max_before": [],
            "max_coloring": [],
            "min_before": [],
            "min_coloring": []
        }

        for item in items:
            self.logger.info(glob.glob(f'{path}/images/*/before/{item["id"]}.*'))
            if glob.glob(f'{path}/images/*/before/{item["id"]}.*'):
                img_path = glob.glob(f'{path}/images/*/before/{item["id"]}.*')[0].replace(
                    "\\", "/"
                )
                patient_id = img_path.split("images/")[-1].split("/before")[0]
                images_paths = glob.glob(f"{path}/images/{patient_id}/*/*.*")

                image_groups = self.group_by_resolution(images_paths)

                tmp_item = item.copy()
                for type_, group_images in zip(paths.keys(), image_groups):
                    paths[type_] += group_images
                    for img_path in group_images:
                        tmp_item["id"] = img_path.split("/")[-1].split(".")[0]
                        annotations[type_]["items"].append(tmp_item.copy())

        # self.logger.warning(paths)
        # self.logger.warning(annotations)

        task_configs = {
            "max_before": {
                "task_name": f"Task (Before Cleaning{task_type_suffix})",
                "project_id": 1
            },
            "max_coloring": {
                "task_name": f"Task (Colored{task_type_suffix})",
                "project_id": 1
            },
            "min_before": {
                "task_name": f"Task (Before Cleaning, Mobile{task_type_suffix})",
                "project_id": 6
            },
            "min_coloring": {
                "task_name": f"Task (Colored, Mobile{task_type_suffix})",
                "project_id": 6
            }
        }

        for type_ in task_configs.keys():
            if not paths[type_]:
                continue

            self._create_task(
                path,
                annotations[type_],
                paths[type_],
                assignee_id,
                type=type_,
                **task_configs[type_]
            )

        with self.make_client() as client:
            client.tasks.remove_by_ids([task_id])
        shutil.rmtree(path)


if __name__ == "__main__":
    cvat_adapter = CVATAdapter(
        host=os.getenv("CVAT_HOST"),
        user=os.getenv("CVAT_USER"),
        password=os.getenv("CVAT_PASSWORD"),
        logger=logging.getLogger(__name__),
    )
