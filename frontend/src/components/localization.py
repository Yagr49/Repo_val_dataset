import streamlit as st


def localization():
    css = """
    <style>
        [data-testid="stFileUploaderDropzone"] div div::before {{content: "Перетащите изображения сюда"}}
        [data-testid="stFileUploaderDropzone"] div div span {{display: none}}
        [data-testid="stFileUploaderDropzone"] div div::after {{font-?size: .8em; content: "Ограничение: 200MB на файл"}}
        [data-testid="stFileUploaderDropzone"] div div small {{display:none}}
        [data-testid="stFileUploaderPagination"] small {{text-indent: -9999px;line-height: 0}}
        [data-testid="stFileUploaderPagination"] small::after {{text-indent: 0;line-height: 1.25;display: block;content: "Страницы"}}
        [data-testid="stFileUploaderFileErrorMessage"] {{display:none}}
        [data-testid="stFileUploaderDropzone"] button {{text-indent: -9999px;ine-height: 0}}
        [data-testid="stFileUploaderDropzone"] button::after {{text-indent: 0;line-height: initial;display: block;content: "Выбрать"}}
        .element-container:has(
            iframe[title="streamlit_js_eval.streamlit_js_eval"]
        ) {{
            display: none
        }}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)
