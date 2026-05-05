import sqlite3

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Основна таблиця юзерів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                coins INTEGER DEFAULT 0,
                messages INTEGER DEFAULT 0,
                last_card_time REAL DEFAULT 0
            )
        """)
        # Таблиця колекції (хто чию карту має)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection (
                owner_id INTEGER,
                card_id INTEGER,
                rarity TEXT,
                PRIMARY KEY (owner_id, card_id)
            )
        """)
        self.conn.commit()

    def update_user(self, user_id, name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user_id, name))
        cursor.execute("UPDATE users SET messages = messages + 1, name = ? WHERE id = ?", (name, user_id))
        self.conn.commit()

    def manual_add_user(self, user_id, name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)", (user_id, name))
        self.conn.commit()

    def add_to_collection(self, owner_id, card_id, rarity):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO collection (owner_id, card_id, rarity) VALUES (?, ?, ?)", 
                       (owner_id, card_id, rarity))
        self.conn.commit()

    def get_user_collection_stats(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT rarity, COUNT(*) FROM collection WHERE owner_id = ? GROUP BY rarity", (user_id,))
        return dict(cursor.fetchall())

    def get_total_collected(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM collection WHERE owner_id = ?", (user_id,))
        return cursor.fetchone()[0]

    def reset_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET coins = 0, messages = 0 WHERE id = ?", (user_id,))
        cursor.execute("DELETE FROM collection WHERE owner_id = ?", (user_id,))
        self.conn.commit()

    def get_user_data(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT coins, messages FROM users WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        return res if res else (0, 0)

    def get_total_players(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]

    def get_random_user(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM users ORDER BY RANDOM() LIMIT 1")
        return cursor.fetchone()

    def add_coins(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, user_id))
        self.conn.commit()

    def get_last_card_time(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_card_time FROM users WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        return res[0] if res else 0

    def set_last_card_time(self, user_id, timestamp):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET last_card_time = ? WHERE id = ?", (timestamp, user_id))
        self.conn.commit()
