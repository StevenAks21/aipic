import os
import sys
import mariadb

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "pass")
DB_NAME = os.environ.get("DB_NAME", "ai_detector")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def get_connection():
    try:
        conn = mariadb.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
   
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(512) NOT NULL,
                is_admin TINYINT DEFAULT 0,
                high_score INT
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS uploaded_images (
                id INT PRIMARY KEY AUTO_INCREMENT,
                filename VARCHAR(255) NOT NULL,
                s3_key VARCHAR(512) NOT NULL,
                prediction VARCHAR(50),
                confidence FLOAT,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_prediction VARCHAR(50),
                user_id INT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)

        cursor.execute("""
            INSERT INTO users (username, password, is_admin)
            VALUES ('admin', SHA2('admin',512), 1), ('user', SHA2('user',512), 0);
        """)
        conn.commit()
        print("Database initialized successfully.")
    except mariadb.Error as e:
        print(f"DB init failed: {e}")
    finally:
        conn.close()

init_db()
