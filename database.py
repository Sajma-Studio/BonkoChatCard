import psycopg2

class Database:
    def __init__(self, db_url):
        # Підключаємося до хмарної бази PostgreSQL
        self.conn = psycopg2.connect(db_url, sslmode='require')
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cursor:
            # Таблиця користувачів
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    name TEXT,
                    coins INTEGER DEFAULT 0,
                    messages INTEGER DEFAULT 0,
                    last_card_time DOUBLE PRECISION DEFAULT 0
                )
            """)
            # Таблиця колекції
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection (
                    owner_id BIGINT,
                    card_id BIGINT,
                    rarity TEXT,
                    PRIMARY KEY (owner_id, card_id)
                )
            """)
            self.conn.commit()

    # --- НОВІ МЕТОДИ ДЛЯ ОНОВЛЕННЯ ---

    def get_top_rich(self, limit=10):
        """Отримує список найбагатших гравців"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT name, coins FROM users ORDER BY coins DESC LIMIT %s", (limit,))
            return cursor.fetchall()

    def set_coins(self, user_id, amount):
        """Встановлює конкретну кількість монет (для адмінів)"""
        with self.conn.cursor() as cursor:
            cursor.execute("UPDATE users SET coins = %s WHERE id = %s", (amount, user_id))
            self.conn.commit()

    # --- ІСНУЮЧІ МЕТОДИ (БЕЗ ЗМІН) ---

    def update_user(self, user_id, name):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (id, name, messages) VALUES (%s, %s, 1)
                ON CONFLICT (id) DO UPDATE SET 
                messages = users.messages + 1, name = EXCLUDED.name
            """, (user_id, name))
            self.conn.commit()

    def manual_add_user(self, user_id, name):
        with self.conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (id, name) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING", (user_id, name))
            self.conn.commit()

    def add_to_collection(self, owner_id, card_id, rarity):
        with self.conn.cursor() as cursor:
            cursor.execute("INSERT INTO collection (owner_id, card_id, rarity) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                           (owner_id, card_id, rarity))
            self.conn.commit()

    def get_user_collection_stats(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT rarity, COUNT(*) FROM collection WHERE owner_id = %s GROUP BY rarity", (user_id,))
            return dict(cursor.fetchall())

    def get_total_collected(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM collection WHERE owner_id = %s", (user_id,))
            return cursor.fetchone()[0]

    def reset_user(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute("UPDATE users SET coins = 0, messages = 0 WHERE id = %s", (user_id,))
            cursor.execute("DELETE FROM collection WHERE owner_id = %s", (user_id,))
            self.conn.commit()

    def get_user_data(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT coins, messages FROM users WHERE id = %s", (user_id,))
            res = cursor.fetchone()
            return res if res else (0, 0)

    def get_total_players(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            return cursor.fetchone()[0]

    def get_random_user(self):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT id, name FROM users ORDER BY RANDOM() LIMIT 1")
            return cursor.fetchone()

    def add_coins(self, user_id, amount):
        with self.conn.cursor() as cursor:
            cursor.execute("UPDATE users SET coins = coins + %s WHERE id = %s", (amount, user_id))
            self.conn.commit()

    def get_last_card_time(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT last_card_time FROM users WHERE id = %s", (user_id,))
            res = cursor.fetchone()
            return res[0] if res else 0

    def set_last_card_time(self, user_id, timestamp):
        with self.conn.cursor() as cursor:
            cursor.execute("UPDATE users SET last_card_time = %s WHERE id = %s", (timestamp, user_id))
            self.conn.commit()
