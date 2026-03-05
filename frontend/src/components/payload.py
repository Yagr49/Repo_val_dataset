import streamlit as st


def payload(payload_id: str, amount: int, date: str, status: str, theme, location):
    if not theme or not location:
        return

    origin = location["origin"]

    html = f"""
        <style>
        .loader {{
            width: 23px;
            height: 23px;
            border: 3px solid #372579;
            border-bottom-color: transparent;
            border-radius: 50%;
            display: inline-block;
            box-sizing: border-box;
            animation: rotation 1s linear infinite;
        }}
        @keyframes rotation {{
            0% {{
                transform: rotate(0deg);
            }}
            100% {{
                transform: rotate(360deg);
            }}
        }}
        .payload {{
            border-radius: 5px;
            background-color: {theme["backgroundColor"]};
            padding: 10px 20px;
            margin-top: 10px;
        }}
        .payload_body {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .failed {{
            border: solid 1px #FF4B4B
        }}
        .button {{
            cursor: pointer;
            margin: 0;
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            width: auto;
            user-select: none;
            background-color: {theme["secondaryBackgroundColor"]};
            border: 1px solid {theme["fadedText10"]};
            text-decoration: none;
            color: {theme["textColor"]};
            margin-top: 10px;
            display: inline-block;
        }}
        .button:visited {{
            color: {theme["textColor"]};
        }}
        .button:hover {{
            color: rgb(255, 75, 75);
            text-decoration: none;
            border-color: rgb(255, 75, 75);
        }}
        </style>
        <div class="payload {"failed" if (status == "rejected" or status == "edited") else ""}">
            <div class="payload_body">
                <div>
                    <div>
                        №{payload_id}
                    </div>
                    <div>
                        {amount}
                    </div>
                    <div>
                        {date}
                    </div>
                </div>
                {'<div class="loader"></div>' if status == "pending" else
                    f'<img src="app/static/{"fail" if (status == "edited" or status == "rejected") else "success"}.png"></img>'
                }
            </div>
            {f'<a class="button" href="{origin}/edit?id={payload_id}">Редактировать</a' if status == "rejected" else ""}
        </div>
    """
    st.html(html)
