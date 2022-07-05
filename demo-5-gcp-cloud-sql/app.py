import random
import pymysql
import requests
from flask import Flask, jsonify
from google.cloud import secretmanager_v1
from datetime import datetime

app = Flask(__name__)

DB_INSTANCE_NAME = "proto-sql"
DB_HOST = "192.168.10.3"
DB_USER = "postgres"
DB_DATABASE = "sales"
#DB_PASSWORD = "passw0rd" # don't do this. instead read it from secret manager

db_password = "bima-pass"

secret_manager_client = secretmanager_v1.SecretManagerServiceClient()

def get_db_password_from_secrets_manager():

    # query secret manager to get the secret

    db_pwd_secret = secret_manager_client.access_secret_version(
        name=f"projects/489083022504/secrets/{db_password}/versions/latest"
    )

    db_pwd = db_pwd_secret.payload.data.decode('UTF-8')

    return db_pwd


DB_PASSWORD = get_db_password_from_secrets_manager()


def get_project_id():
    METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/'
    METADATA_HEADERS = {'Metadata-Flavor': 'Google'}

    try:
        url = METADATA_URL + 'project/project-id'
        resp = requests.get(
            url,
            headers=METADATA_HEADERS)
        print("Project id is {}".format(resp.text))
        return resp.text
    except requests.exceptions.ConnectionError:
        return "XXX"


def get_connection_unix_socket():
    print("getting connection unix socket")

    db_socket_dir = "/cloudsql"
    cloud_sql_connection_name = f"{get_project_id()}:us-central1:{DB_INSTANCE_NAME}"

    print(f"db_socket_dir: {db_socket_dir}")
    print(f"cloud_sql_connection_name: {cloud_sql_connection_name}")

    return pymysql.connect(unix_socket=f"/{db_socket_dir}/{cloud_sql_connection_name}",
                           user=DB_USER,
                           password=DB_PASSWORD,
                           database=DB_DATABASE,
                           cursorclass=pymysql.cursors.DictCursor)


def get_connection():
    print("getting connection")

    return pymysql.connect(host=DB_HOST,
                           user=DB_USER,
                           password=DB_PASSWORD,
                           database=DB_DATABASE,
                           cursorclass=pymysql.cursors.DictCursor)


def insert_into_db_over_public_ip():
    connection = get_connection_unix_socket()

    with connection:
        with connection.cursor() as cursor:
            for _ in range(5):
                item_id = random.randrange(1, 100)
                units = random.randrange(101, 1001)
                sql = f"INSERT INTO `sales_data` (`itemid`, `units`, `insertedon`, `insertedover`) VALUES ({item_id}, {units},'{datetime.now()}','public ip')"
                cursor.execute(sql)
        connection.commit()


def insert_into_db_over_private_ip():
    connection = get_connection()

    with connection:
        with connection.cursor() as cursor:
            for _ in range(5):
                item_id = random.randrange(101, 200)
                units = random.randrange(201, 2001)
                sql = f"INSERT INTO `sales_data` (`itemid`, `units`, `insertedon`, `insertedover`) VALUES ({item_id}, {units},'{datetime.now()}','private ip')"
                cursor.execute(sql)
        connection.commit()


@app.route("/connect-over-public-ip", methods=["GET"])
def load_data_in_db_over_public_ip():
    insert_into_db_over_public_ip()
    return jsonify(message="inserted over public IP"), 200


@app.route("/connect-over-private-ip", methods=["GET"])
def load_data_in_db_over_private_ip():
    insert_into_db_over_private_ip()
    return jsonify(message="inserted over private IP"), 200


if __name__ == '__main__':
    insert_into_db_over_public_ip()
