import asyncio
import time
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from database import Database

# --- ФІКТИВНИЙ СЕРВЕР ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Sajma Studio Bot is running!"

def run():
    # Render використовує порт 10000 за замовчуванням
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --- НАЛАШТУВАННЯ БОТА ---
TOKEN = "8161816299:AAG_x1WArl0oQviMYF77UChNJJ4uygdH7YM"
MY_ID = 7518373450
OWNER_ID = 6810492221
COOLDOWN = 60

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database("db.sqlite")

@dp.message(F.text)
async def handle_msg(message: types.Message):
    if message.from_user and not message.text.startswith('/'):
        db.update_user(message.from_user.id, message.from_user.full_name)

    if message.text == "/get":
        await get_card(message)
    elif message.text == "/balance":
        coins, messages = db.get_user_data(message.from_user.id)
        await message.reply(f"💰 Твій баланс: {coins} монет\n✉️ Всього повідомлень: {messages}")

async def get_card(message: types.Message):
    user_id = message.from_user.id
    now = time.time()
    last_time = db.get_last_card_time(user_id)
    
    if now - last_time < COOLDOWN:
        remains = int(COOLDOWN - (now - last_time))
        await message.reply(f"⏳ Зачекай ще {remains} сек.!")
        return

    target = db.get_random_user()
    if not target:
        await message.reply("У базі ще немає гравців!")
        return

    tid, tname = target
    if tid == MY_ID:
        rarity, bonus = "🛠 УНІКАЛЬНА (Розробник)", 100
    elif tid == OWNER_ID:
        rarity, bonus = "👑 КОРОЛІВСЬКА (Власник)", 100
    else:
        rarity, bonus = db.get_rarity_info(tid)

    db.add_coins(user_id, bonus)
    db.set_last_card_time(user_id, now)
    new_coins, _ = db.get_user_data(user_id)

    try:
        user_photos = await bot.get_user_profile_photos(tid, limit=1)
        photo = user_photos.photos[0][-1].file_id if user_photos.total_count > 0 else "https://i.imgur.com/KzS6CqC.png"
    except Exception:
        photo = "https://i.imgur.com/KzS6CqC.png"

    caption = (
        f"🌟 **Вітаю, тобі випала картка {tname}!**\n\n"
        f"✨ Рідкість: {rarity}\n"
        f"💰 Бонус: +{bonus} монет\n"
        f"💳 Твій баланс: {new_coins} 🪙"
    )
    await message.answer_photo(photo=photo, caption=caption, parse_mode="Markdown")

async def main():
    # Запускаємо вебсервер у фоновому потоці
    keep_alive()
    print("Бот Sajma Studio запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
