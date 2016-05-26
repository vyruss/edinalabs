import csv
import os
import platform
import string

import psycopg2


class DatabaseConnectionParams:
    def __init__(self, host, port, dbname, user):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = self.get_password()

    def get_password(self):
        password = None

        system_type = platform.system()

        if system_type in ('Linux', 'Windows'):
            if system_type == 'Linux':
                pg_passw_fname = ''.join([os.getenv('HOME'), '/.pgpass'])
            else:
                pg_passw_fname = os.path.join(os.getenv('APPDATA'), 'postgresql', 'pgpass.conf')

            if os.path.exists(pg_passw_fname):
                with open(pg_passw_fname, 'r') as f:
                    pg_connections = csv.reader(f, delimiter=':')
                    for conn in pg_connections:
                        if conn[0] == self.host and conn[1] == self.port and conn[3] == self.user:
                            password = conn[4]

        return password

    def get_connection_string(self):
        connection_string = None
        if self.password is not None:
            pg_conn_t = string.Template("""host=$host port=$port dbname=$dbname user=$user password=$password""")
            connection_string = pg_conn_t.substitute(host=self.host,
                                                     port=self.port,
                                                     dbname=self.dbname,
                                                     user=self.user,
                                                     password=self.password)

        return connection_string


def query_pg(db_connection_string, sql):
    """
        connect to pg, run sql, return the records as a list
    """
    records = []

    if db_connection_string is not None:
        try:
            conn = psycopg2.connect(db_connection_string)
            try:
                cur = conn.cursor()
                cur.execute(sql)
                for record in cur:
                    records.append(record)
            except Exception:
                print(Exception)
            finally:
                cur.close()
        except Exception:
            print(Exception)
        finally:
            conn.close()

    return records


def update_pg(sql, db_connection_string):
    """
        connect to pg, run sql, return the records as a list
    """

    if db_connection_string is not None:
        try:
            conn = psycopg2.connect(db_connection_string)
            try:
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
            except Exception:
                print(Exception)
            finally:
                cur.close()
        except Exception:
            print(Exception)
        finally:
            conn.close()
