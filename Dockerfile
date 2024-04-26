# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.10.12

ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_HOST
ARG POSTGRES_PORT
ARG POSTGRES_DB



FROM postgres:9.4
COPY docker-entrypoint-initdb.d/init.sql /docker-entrypoint-initdb.d/init.sql
EXPOSE 5432
CMD ["postgres"] 



FROM python:${PYTHON_VERSION}-slim as base
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
COPY example.env .env
RUN pip install -r requirements.txt
# Expose the port that the application listens on.
EXPOSE 5000
# Run the application.
ENV FLASK_APP='app/app.py'
CMD ["flask", "run", "--host=0.0.0.0"]



