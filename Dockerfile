# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.10.12

# ARG POSTGRES_USER
# ARG POSTGRES_PASSWORD
# ARG POSTGRES_HOST
# ARG POSTGRES_PORT
# ARG POSTGRES_DB
# FROM postgres:9.4
# COPY docker-entrypoint-initdb.d/init.sql /docker-entrypoint-initdb.d/init.sql
# EXPOSE 5432
# CMD ["postgres"] 

ARG MYSQL_USER
ARG MYSQL_PASSWORD
ARG MYSQL_HOST
ARG MYSQL_PORT
ARG MYSQL_DATABASE

FROM mysql:8.0
ENV MYSQL_USER=$MYSQL_USER
ENV MYSQL_PASSWORD=$MYSQL_PASSWORD
ENV MYSQL_HOST=$MYSQL_HOST
ENV MYSQL_PORT=$MYSQL_PORT
ENV MYSQL_DATABASE=$MYSQL_DATABASE

# Install necessary packages for Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    apt-get clean
# Install pymysql and cryptography
RUN pip3 install pymysql cryptography
EXPOSE 3306
CMD ["mysqld", "--default-authentication-plugin=mysql_native_password"]




FROM python:${PYTHON_VERSION}-slim as base
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
# COPY example.env .env
COPY example.env .env
RUN pip install -r requirements.txt
RUN pip install pymysql cryptography
# Expose the port that the application listens on.
EXPOSE 5000
# Run the application.
ENV FLASK_APP='app/app.py'
CMD ["flask", "run", "--host=0.0.0.0"]



