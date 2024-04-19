# control_db

#BASE
apt-get install python3
virtualenv .venv
source .venv/bin/activate

#REQ
pip install -r requirements.txt
docker volume create --name db_volume
docker run -d --name postgres -p 5432:5432 --env-file database.conf -v db_volume:/var/lib/postgresql postgres:latest

#EXEC
export $(xargs < database.conf)
export FLASK_APP=src/app/app.py
flask run