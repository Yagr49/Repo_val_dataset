FROM python:3.10-slim

ARG PORT
ENV PORT=${PORT}
ENV PIP_INSTALL="python -m pip --no-cache-dir install --upgrade"
EXPOSE ${PORT}

RUN apt -y update && apt -y upgrade
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

COPY requirements.txt .
RUN $PIP_INSTALL -r requirements.txt
COPY src .
CMD ["sh", "-c", "streamlit run ./main.py --server.port=${PORT} --server.address=0.0.0.0 --server.runOnSave=true --client.showSidebarNavigation=false --server.enableStaticServing=true"]
