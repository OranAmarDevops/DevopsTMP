FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY settings.py logging_setup.py ./
COPY frontend ./frontend

EXPOSE 5000

CMD ["python", "-m", "frontend.app"]
