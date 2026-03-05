import streamlit as st


def photo_display(files, dynamic_columns=True, init_display=None, comments=[]):
    if len(files) < 3 and init_display is None:
        init_display = len(files)
    elif init_display is None:
        init_display = 3
    contains_bad_photos = False
    display_columns = (
        st.number_input("Количество колонок:", 1, 5, init_display)
        if dynamic_columns
        else init_display
    )

    groups = []

    for i in range(0, len(files), display_columns):
        groups.append(files[i: i + display_columns])

    for group in groups:
        cols = st.columns(display_columns)
        for i, image in enumerate(group):
            try:
                if image.name:
                    cols[i].write(image.name)

            except Exception as e:
                print(e)
            try:
                cols[i].image(image)
            except Exception as e:
                print(e)
                contains_bad_photos = True
                cols[i].caption("Невозможно отобразить файл")
            try:
                if comments[i] is not None:
                    with cols[i]:
                        st.error(comments[i])
            except Exception as e:
                print(e)
    return contains_bad_photos
