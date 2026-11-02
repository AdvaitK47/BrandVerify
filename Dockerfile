FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
COPY backend/requirements-advanced.txt ./backend/requirements-advanced.txt

RUN python -m pip install --upgrade pip \
    && pip install -r ./backend/requirements.txt \
    && pip install -r ./backend/requirements-advanced.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 10000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
