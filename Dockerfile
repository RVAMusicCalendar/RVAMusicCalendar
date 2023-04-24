FROM python:3.12.0a7
RUN apt-get update && apt-get install -y \
    cron \
    gconf-service \
    libasound2 \
    libatk1.0-0  \
    libcairo2 \
    libcups2 \
    libfontconfig1  \
    libgdk-pixbuf2.0-0  \
    libgtk-3-0 \
    libnspr4  \
    libpango-1.0-0 \
    libxss1  \
    fonts-liberation \
    libappindicator1  \
    libnss3 \
    lsb-release \
    xdg-utils

#download and install chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

RUN rm -rf /var/lib/aptlists

RUN pip3 install --upgrade pip

RUN mkdir /app
COPY ./src /app
COPY pyproject.toml /app

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
RUN pip3 install chromedriver-binary-auto

COPY service.json /app

CMD ["python", "/app/main.py"]