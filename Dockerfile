FROM python:3.8-slim-buster

WORKDIR /app
COPY pip.conf pip.conf
ENV PIP_CONFIG_FILE pip.conf
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . .


CMD [ "uvicorn", "main:app" , "--port", "8676", "--host", "0.0.0.0"]

