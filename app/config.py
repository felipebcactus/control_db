from dotenv import dotenv_values
config = dotenv_values(".env")

# user = config["POSTGRES_USER"]
# password = config["POSTGRES_PASSWORD"]
# host = config["POSTGRES_HOST"]
# database = config["POSTGRES_DB"]
# port = config["POSTGRES_PORT"]

__user = config["MYSQL_USER"]
__password = config["MYSQL_PASSWORD"]
__host = config["MYSQL_HOST"]
__port = config["MYSQL_PORT"]
__database = config["MYSQL_DATABASE"]

# DATABASE_CONNECTION_URI = f'postgresql+psycopg2://{__user}:{__password}@{__host}:{__port}/{__database}'
DATABASE_CONNECTION_URI = f'mysql+pymysql://{__user}:{__password}@{__host}:{__port}/{__database}'
print(">>>>> "+DATABASE_CONNECTION_URI)
