import asyncio
import multiprocessing
from backend.db_service import send_cvat_tag, export_cvat
import logging
import streamlit as st
from backend.repo.patient import PatientRepo


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


class CvatProcessor:
    @staticmethod
    async def _send_to_cvat():
        """Асинхронная задача для отправки тегов в CVAT"""
        while True:
            await asyncio.sleep(10)
            logger.info("++++++++++")
            try:
                send_cvat_tag(PatientRepo.get_not_sent_cases(), task_name="Tagging")
                send_cvat_tag(PatientRepo.get_not_sent_cases_type_3(), task_name="Tagging, Type III")
            except Exception as e:
                logger.error(f"Error in send_to_cvat: {e}")

    @staticmethod
    async def _check_export_from_cvat():
        """Асинхронная задача для проверки экспорта из CVAT"""
        while True:
            await asyncio.sleep(10)
            logger.info("++++++++++")

            try:
                export_cvat()
            except Exception as e:
                logger.exception(f"Error in check_export_from_cvat: {e}", exc_info=True)

    async def _main(self):
        """Основная асинхронная точка входа"""
        await asyncio.gather(
            self._send_to_cvat(),
            self._check_export_from_cvat()
        )

    def run(self):
        """Запуск всего процесса"""
        asyncio.run(self._main())


@st.cache_resource
def run_background_processor():
    processor = CvatProcessor()
    process = multiprocessing.Process(target=processor.run)
    try:
        logger.info("Start process...")
        process.start()
    except KeyboardInterrupt:
        logger.info("Stopping...")
        process.terminate()
    # finally:
    # if process.is_alive():
        process.close()
