from mysql.connector import pooling
from contextlib import contextmanager
import os
import json
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()


class DataBaseManager:
    def __init__(self):
        self.pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=10,
            pool_reset_session=True,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )

    def get_connection(self):
        return self.pool.get_connection()

    @contextmanager
    def _cursor(self, dictionary=False):
        conn = self.get_connection()

        try:
            # dictionary=True lets callers get rows back as {"col": val} instead of tuples
            cursor = conn.cursor(dictionary=dictionary)
            yield cursor
            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def upload_valid_data(self, valid_data):
        try:
            with self._cursor() as cursor:

                query = """
                    INSERT INTO valid_data (recipient_name, address, status)
                    VALUES ( %s, %s, %s)
                """

                values = [
                    (
                        
                        item["row"]["recipient_name"],
                        item["row"]["address"],
                        item["row"]["status"]
                    )
                    for item in valid_data
                ]
                logger.info("Starting valid data upload")
                cursor.executemany(query, values)
                logger.info("Finish valid data upload succesfully")
        except Exception as e:
            raise ValueError(f"Error while uploading valid data: {e}")

    def upload_invalid_data(self, invalid_data):
        try:
            with self._cursor() as cursor:

                query = """
                    INSERT INTO invalid_data (track_id, row_num, raw_row, errors)
                    VALUES (%s, %s, %s, %s)
                """

                values = [
                    (
                        item["track_id"],
                        item["row_number"],
                        json.dumps(item["raw_row"]),
                        json.dumps(item["errors"])
                    )
                    for item in invalid_data
                ]
                logger.info("Starting invalid data upload")
                cursor.executemany(query, values)
                logger.info("Finish invalid data upload succesfully")
                

        except Exception as e:
            raise ValueError(f"Error while uploading invalid data: {e}")

    def upload_imports(self,track_id, v_counter, inv_counter, row_counter, filename):
        try:
            with self._cursor() as cursor:
                query="""
                    INSERT INTO imports (track_id, total_rows, valid_rows, invalid_rows, filename)
                    VALUES (%s, %s, %s, %s, %s)
                """
                values =(
                    track_id, row_counter, v_counter, inv_counter, filename
                )
                logger.info("Starting upload import")
                cursor.execute(query, values)
                logger.info("upload import finished")
        except Exception as e:
            raise ValueError(f"error occured due to {e}")
    def get_imports(self):
        try:
            with self._cursor() as cursor:

                cursor.execute(
                    "select * from imports"
                )
                result = cursor.fetchall()
                logger.info("imports selected succefully")
                return result
        except Exception as e:
            raise ValueError(f"error occured due to {e}")

    def get_user_by_username(self, username):
        try:
            # dictionary=True: deps.py/app.py read this row via user["role"] etc., not by index
            with self._cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT * From users WHERE username = %s", (username,)
                )
                result= cursor.fetchone()
                return result
        except Exception as e:
            raise ValueError(f"Error occured due to {e}")
        
db = DataBaseManager()

