FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \

    python3-dev \

    python3-pip \

    python3-cffi \

    libcairo2 \

    libpango-1.0-0 \

    libpangocairo-1.0-0 \

    libgdk-pixbuf-2.0-0 \

    libffi-dev \

    shared-mime-info \

    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . /app/