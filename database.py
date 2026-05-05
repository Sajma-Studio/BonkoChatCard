import sqlite3

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        with self.connection:
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                msg_count INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                last_card_time REAL DEFAULT 0
            )""")

    def update_user(self, user_id, username):
        with self.connection:
            self.cursor.execute("""
            INSERT INTO users (user_id, username, msg_count) 
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET 
                msg_count = msg_count + 1,
                username = EXCLUDED.username
            """, (user_id, username))

    def add_coins(self, user_id, amount):
        with self.connection:
            self.cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))

    def get_user_data(self, user_id):
        res = self.cursor.execute("SELECT coins, msg_count FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return res if res else (0, 0)

    def get_rarity_info(self, target_id):
        users = self.cursor.execute("SELECT user_id FROM users ORDER BY msg_count DESC").fetchall()
        user_ids = [u[0] for u in users]
        if target_id not in user_ids: return "⚪ Звичайна", 5
        rank = user_ids.index(target_id) + 1
        if rank == 1: return "💎 ЛЕГЕНДАРНА", 50
        elif 2 <= rank <= 5: return "🔥 ЕПІЧНА", 10
        else: return "⚪ Звичайна", 5

    def get_random_user(self):
        return self.cursor.execute("SELECT user_id, username FROM users ORDER BY RANDOM() LIMIT 1").fetchone()

    def get_last_card_time(self, user_id):
        res = self.cursor.execute("SELECT last_card_time FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return res[0] if res else 0

    def set_last_card_time(self, user_id, t):
        with self.connection:
            self.cursor.execute("UPDATE users SET last_card_time = ? WHERE user_id = ?", (t, user_id))
