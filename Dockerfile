FROM python:3.12.0a7
RUN apt-get update && apt-get install -y \
    cron \
 && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install poetry

RUN mkdir /app
COPY ./src /app
COPY pyproject.toml /app

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
COPY service.json /app

CMD ["python", "/app/main.py"]
#COPY crontab crontab
#RUN crontab crontab
#CMD ["cron", "-f"]