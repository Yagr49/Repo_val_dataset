import pathlib
import datetime

import pandas as pd

import streamlit as st
from dateutil.relativedelta import relativedelta
from streamlit_theme import st_theme

from backend_func import get_stats
from components.authenticate import authenticate
from components.logout import logout
from components.nav import nav
from utils import is_admin

mapping_group = {
    0: 'Дети возрастом 7 лет',
    1: 'Группа № 1 - Дети младше 7 лет',
    2: 'Группа № 2 - Дети старше 7 лет',
    3: 'Группа № 3',
    4: 'Группа № 4'
}

# Title and favicon
st.set_page_config(
    page_title="Статистика", page_icon=f"{pathlib.Path().resolve()}/static/favicon.ico"
)


# Authentication and authorization
authenticate()

if "keycloak_roles" not in st.session_state:
    st.stop()

if not is_admin():
    st.switch_page("main.py")


# Getting page information using components
theme = st_theme()


# Sidebar
with st.sidebar:
    logout(theme)
    nav()


# Page
st.header("Статистика")

try:
    offset = datetime.timedelta(hours=3)
    tz = datetime.timezone(offset, name="МСК")
    (start_date, end_date) = st.date_input(
        "Укажите период",
        value=(
            datetime.datetime.now(tz=tz) - relativedelta(days=7),
            datetime.datetime.now(tz=tz),
        ),
        max_value=datetime.datetime.now(tz=tz),
        min_value=datetime.datetime.strptime("01/10/2024", "%d/%m/%Y"),
    )
except Exception as e:
    print(e)
    st.stop()

cases = get_stats(start_date, end_date)
if st.button("Обновить"):
    cases = get_stats(start_date, end_date)

accepted = 0
rejected = 0
pending = 0
total = 0
for case in cases:
    for doctor in case:
        accepted += doctor["accepted"]
        rejected += doctor["rejected"]
        pending += doctor["pending"]
        total += doctor["total"]

st.subheader("Всего за период")

(c1, c2, c3, c4) = st.columns(4)
c1.metric("Принято", value=accepted)
c2.metric("Не принято", value=rejected)
c3.metric("В обработке", value=pending)
c4.metric("Всего", value=total)

for i, case in enumerate(cases):
    st.subheader(f"{mapping_group.get(i)}")

    table = []
    accepted = 0
    rejected = 0
    pending = 0
    total = 0

    for doctor in case:
        accepted += doctor["accepted"]
        rejected += doctor["rejected"]
        pending += doctor["pending"]
        total += doctor["total"]
        table.append([*doctor.values()])

    (c1, c2, c3, c4) = st.columns(4)
    c1.metric("Принято", value=accepted)
    c2.metric("Не принято", value=rejected)
    c3.metric("В обработке", value=pending)
    c4.metric("Всего", value=total)

    df = pd.DataFrame(
        data=table, columns=["Врач", "Принято", "Не принято", "В обработке", "Всего"]
    )

    st.dataframe(df, hide_index=True)
