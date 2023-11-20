FROM python:3.12
RUN apt-get update && apt-get install -y \
    cron \
    gconf-service
#    wkhtmltopdf # needed for imgkit to generate images
#    libasound2 \
#    libatk1.0-0  \
#    libcairo2 \
#    libcups2 \
#    libfontconfig1  \
#    libgdk-pixbuf2.0-0  \
#    libgtk-3-0 \
#    libnspr4  \
#    libpango-1.0-0 \
#    libxss1  \
#    fonts-liberation \
#    libappindicator1  \
#    libnss3 \
#    lsb-release \
#    xdg-utils \

##download and install chrome
#RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
#RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install
#
#RUN rm -rf /var/lib/aptlists
ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1

RUN pip3 install --upgrade pip

RUN mkdir /app
WORKDIR /app
COPY pyproject.toml /app

ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false

RUN poetry install --no-dev

COPY ./src /app

#COPY service.json /app

CMD ["python", "/app/main.py"]