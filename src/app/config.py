from dotenv import dotenv_values
config = dotenv_values(".env")

user = config["POSTGRES_USER"]
password = config["POSTGRES_PASSWORD"]
host = config["POSTGRES_HOST"]
database = config["POSTGRES_DB"]
port = config["POSTGRES_PORT"]

DATABASE_CONNECTION_URI = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'
