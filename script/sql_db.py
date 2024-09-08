import mysql.connector

def db_connection(host, user, password, database):
    """Connect to MySQL database.

    :param host: hostname or ip address of mysql server
    :param user: username to use for connection
    :param password: password to use for connection
    :param database: database name to use
    :return: a database connection
    """
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )


def iot_223():
    return db_connection('192.168.15.223', 'admin', 'itbekasioke', 'iot')


def parkir_220():
    return db_connection('192.168.15.220', 'user_external_220', 'Sttbekasioke123!', 'parkir')


def db_pegawai_220():
    return db_connection('192.168.15.220', 'user_external_220', 'Sttbekasioke123!', 'db_pegawai')