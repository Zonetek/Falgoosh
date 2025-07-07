FROM python:3.11-slim
WORKDIR /app

COPY requirements/scanner.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY api_applications/ ./api_applications/

WORKDIR /app/api_applications
