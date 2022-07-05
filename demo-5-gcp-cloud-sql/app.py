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
DB_DATABASE = "postgres"
DB_PASSWORD = "inipassword"


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
