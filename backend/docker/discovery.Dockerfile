FROM python:3.11-slim
WORKDIR /app

COPY requirements/base.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY api_applications/discovery/ .

CMD ["python", "scanner.py"]
