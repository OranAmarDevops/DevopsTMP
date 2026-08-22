FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY settings.py config.json ./
COPY backend ./backend

EXPOSE 5001

CMD ["python", "-m", "backend.app"]