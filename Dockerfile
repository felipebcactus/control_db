# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/go/dockerfile-reference/

# Want to help us make this template better? Share your feedback here: https://forms.gle/ybq9Krt8jtBL3iCk7

ARG PYTHON_VERSION=3.10.12
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Switch to the non-privileged user to run the application.
USER appuser

FROM library/postgres
ENV POSTGRES_USER='control_user'
ENV POSTGRES_PASSWORD='passw0rd'
ENV POSTGRES_DB='control_user'
COPY /docker-entrypoint-initdb.d/init.sql /docker-entrypoint-initdb.d/init.sql

# Copy the source code into the container.
RUN mkdir ./app
COPY ./app ./app

COPY example.env ./.env

FROM library/python:3.6-stretch

COPY requirements.txt .
COPY teste.sql .
RUN pip install -r requirements.txt

# Expose the port that the application listens on.
EXPOSE 5000

# Run the application.
ENV FLASK_APP='app.py'
CMD ["ls","."]
#CMD ["flask", "run", "--host=0.0.0.0"]
