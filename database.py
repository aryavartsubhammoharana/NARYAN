def _init_mysql():
    import mysql.connector
    # Direct connect to the database without trying to create it
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    c = conn.cursor()
    
    # Aiven already gives you a database, so just use it
    statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            full_name     VARCHAR(150) NOT NULL,
            email         VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            branch        VARCHAR(100),
            roll_number   VARCHAR(50) UNIQUE,
            is_verified   TINYINT(1) DEFAULT 0,
            verify_token  VARCHAR(255),
            reset_token   VARCHAR(255),
            reset_expires DATETIME,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        # ... बाकी सारी टेबल्स वैसी ही रहने दें ...
    ]
    for stmt in statements:
        c.execute(stmt)
    conn.commit()
    conn.close()
