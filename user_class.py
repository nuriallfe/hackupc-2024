import pandas as pd
from sqlalchemy import create_engine, text

class UserManager:
    def __init__(self, username='demo', password='demo', hostname='localhost', port='1972', namespace='USER'):
        """
        Initialize the UserManager class with database connection details.
        """
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.namespace = namespace
        self.engine = None
        self.connect_to_database()
        self.create_user_table()

    def connect_to_database(self):
        """
        Establish a connection to the SQL database.
        """
        CONNECTION_STRING = f"iris://{self.username}:{self.password}@{self.hostname}:{self.port}/{self.namespace}"
        self.engine = create_engine(CONNECTION_STRING)

    def create_user_table(self):
        """
        Create a SQL table to store user information if it doesn't exist.
        """
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INT PRIMARY KEY,
                        preferences VARCHAR(200),
                        visited_places VARCHAR(20000)
                    )
                """))

    def update_user_info(self, user_id, new_preferences=None, new_places=None):
        """
        Update user preferences and visited places in the database.
        """
        with self.engine.connect() as conn:
            with conn.begin():
                if new_preferences:
                    conn.execute(text(f"UPDATE users SET preferences = :preferences WHERE user_id = :user_id"),
                                 {'preferences': new_preferences, 'user_id': user_id})
                if new_places:
                    conn.execute(text(f"UPDATE users SET visited_places = :visited_places WHERE user_id = :user_id"),
                                 {'visited_places': new_places, 'user_id': user_id})

    def add_user(self, user_id, preferences, visited_places):
        """
        Add a new user to the database.
        """
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(text("""
                    INSERT INTO users (user_id, preferences, visited_places)
                    VALUES (:user_id, :preferences, :visited_places)
                """), {'user_id': user_id, 'preferences': preferences, 'visited_places': visited_places})

    def get_user_info(self, user_id):
        """
        Retrieve user information from the database.
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM users WHERE user_id = :user_id"), {'user_id': user_id})
            return result.fetchone()
        
    def get_all_users(self):
        """
        Retrieve information for all users from the database.
        """
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users"))
            return result.fetchall()
        
    def delete_user(self, user_id):
        """
        Delete a user from the database.
        """
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(text(f"DELETE FROM users WHERE user_id = :user_id"), {'user_id': user_id})

    def delete_all_users(self):
        """
        Delete all users from the database.
        """
        with self.engine.connect() as conn:
            with conn.begin():
                conn.execute(text("DELETE FROM users"))