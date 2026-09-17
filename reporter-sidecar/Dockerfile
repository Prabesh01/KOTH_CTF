# Deliberately minimal: no shell tools beyond what the base image has, no
# SSH, no web app, nothing installed beyond Python itself. There is no
# vulnerability here for a player to exploit into -- that's the entire
# point of this container's existence.
FROM python:3.11-slim

COPY koth_reporter.py /app/koth_reporter.py

EXPOSE 9001
CMD ["python3", "/app/koth_reporter.py"]
