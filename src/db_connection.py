import mysql.connector
from mysql.connector import Error

def create_connection():
    """
    Creates and returns a MySQL database connection.
    """
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",          # replace with your MySQL username
            password="",  # replace with your MySQL password
            database="saas_funnel"
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: '{e}'")
        return None

def close_connection(connection):
    """
    Closes the MySQL database connection.
    """
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection closed")

if __name__ == "__main__":
    conn = create_connection()
    if conn:
        close_connection(conn)
