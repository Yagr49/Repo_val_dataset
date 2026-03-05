import streamlit as st

from components.photo_display import photo_display
from config import Config


def file_uploader_segment(title):
    contains_bas_photos = False

    with st.container(border=True):
        st.header(title)

        files = st.file_uploader(
            label="Фотографии:",
            accept_multiple_files=True,
            type=Config.FRONTEND_FILE_ACCEPT.split(","),
            key=f"files{title}{st.session_state.payload_number}",
        )
        if len(files) != 0:
            contains_bas_photos = (
                photo_display(files=files, init_display=2, dynamic_columns=False)
                or contains_bas_photos
            )

    return files, contains_bas_photos
