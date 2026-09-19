FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
COPY webapp/requirements.txt webapp/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r webapp/requirements.txt

COPY bot ./bot
COPY webapp ./webapp

CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
