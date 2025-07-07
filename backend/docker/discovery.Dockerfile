FROM python:3.11-slim
WORKDIR /app

COPY requirements/scanner.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY api_applications/discovery/ .

CMD ["python", "scanner.py"]
