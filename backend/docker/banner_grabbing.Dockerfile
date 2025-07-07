FROM python:3.11-slim
WORKDIR /app

COPY requirements/scanner.txt ./requirements.txt

RUN apt-get update && apt-get install -y nmap && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt

COPY api_applications/ ./api_applications/

WORKDIR /app/api_applications


