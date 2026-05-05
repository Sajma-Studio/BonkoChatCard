import sqlite3

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Таблиця користувачів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                coins INTEGER DEFAULT 0,
                messages INTEGER DEFAULT 0,
                last_card_time REAL DEFAULT 0
            )
        """)
        self.conn.commit()

    def update_user(self, user_id, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET messages = messages + 1, name = ? WHERE id = ?", (name, user_id))
        else:
            cursor.execute("INSERT INTO users (id, name, messages) VALUES (?, ?, 1)", (user_id, name))
        self.conn.commit()

    def manual_add_user(self, user_id, name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", (user_id, name))
        self.conn.commit()

    def get_user_data(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT coins, messages FROM users WHERE id = ?", (user_id,))
        res = cursor.fetchone()
        return res if res else (0, 0)

    def get_user_stats(self):
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

    def get_rarity_info(self, user_id):
        # Проста логіка рідкості (можна ускладнити)
        import random
        r = random.random()
        if r < 0.05: return "🟡 ЛЕГЕНДАРНА", 50
        if r < 0.15: return "🟣 ЕПІЧНА", 30
        if r < 0.40: return "🔵 РІДКІСНА", 15
        return "⚪️ ЗВИЧАЙНА", 5
