# import mysql.connector
import mariadb
from configparser import ConfigParser

def connect_to_database():
    config = ConfigParser()
    config.read('config.cfg')

    db_config = {
        'user': config.get('database', 'user'),
        'password': config.get('database', 'password'),
        'host': config.get('database', 'host'),
        'database': config.get('database', 'database_name')
    }

    try:
        conn = mariadb.connect(**db_config)
        if conn.is_connected():
            print('Berhasil terhubung ke database')
            return conn
    except mariadb.Error as e:
        print(f'Gagal terhubung ke database: {e}')
