FROM python:3.11-slim

RUN pip install --no-cache-dir requests

COPY scorebot.py /scorebot.py
COPY machines.json /config/machines.json

ENTRYPOINT ["python3", "/scorebot.py"]
