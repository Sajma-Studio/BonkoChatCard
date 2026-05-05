import asyncio
import time
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import Database

# Фейковий сервер для стабільної роботи на Render
app = Flask('')
@app.route('/')
def home(): return "Sajma Studio Bot is alive!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive():
    t = threading.Thread(target=run); t.daemon = True; t.start()

# --- КОНФІГУРАЦІЯ ---
TOKEN = "8161816299:AAG_x1WArl0oQviMYF77UChNJJ4uygdH7YM"
MY_ID = 7518373450 
DB_URL = "ВСТАВ_ТУТ_EXTERNAL_DATABASE_URL" # Сюди встав посилання, що починається на postgres://
COOLDOWN = 60

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database(DB_URL)

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🃏 Картка"), KeyboardButton(text="👤 Профіль")]],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Sajma Studio вітає тебе! Починай збирати картки.", reply_markup=get_main_keyboard())

@dp.message(F.text)
async def handle_msg(message: types.Message):
    user_id = message.from_user.id
    
    # Адмін-панель для тебе (Макс)
    if user_id == MY_ID:
        if message.text.startswith("додати"):
            try:
                p = message.text.split(" ", 2)
                db.manual_add_user(int(p[1]), p[2])
                await message.reply(f"✅ Успішно додано {p[2]} в базу!")
            except: await message.reply("Помилка! Формат: `додати ID Ім'я`")
            return
        
        if message.text.startswith("очистити"):
            try:
                target_id = int(message.text.split(" ")[1])
                db.reset_user(target_id)
                await message.reply(f"🧹 Профіль юзера {target_id} очищено.")
            except: await message.reply("Помилка! Формат: `очистити ID`")
            return

    if message.text == "🃏 Картка":
        await get_card(message)
    elif message.text == "👤 Профіль":
        coins, msgs = db.get_user_data(user_id)
        total_in_db = db.get_total_players()
        collected = db.get_total_collected(user_id)
        stats = db.get_user_collection_stats(user_id)
        
        text = (
            f"👤 **Твій профіль:**\n\n"
            f"💰 Баланс: `{coins}`\n"
            f"✉️ Повідомлень: `{msgs}`\n"
            f"🃏 Зібрано унікальних: `{collected}/{total_in_db}`\n\n"
            f"✨ **Рідкості в колекції:**\n"
            f"⚪️ Звичайні: `{stats.get('⚪️ ЗВИЧАЙНА', 0)}` | 🔵 Рідкісні: `{stats.get('🔵 РІДКІСНА', 0)}`\n"
            f"🟣 Епічні: `{stats.get('🟣 ЕПІЧНА', 0)}` | 🟡 Легендарні: `{stats.get('🟡 ЛЕГЕНДАРНА', 0)}`"
        )
        await message.reply(text, parse_mode="Markdown")

    if not message.text.startswith('/'):
        db.update_user(user_id, message.from_user.full_name)

async def get_card(message: types.Message):
    uid = message.from_user.id
    now = time.time()
    
    # Режим "Бога" для тебе: жодних очікувань
    if uid != MY_ID and (now - db.get_last_card_time(uid) < COOLDOWN):
        await message.reply(f"⏳ Кулдаун! Зачекай ще {int(COOLDOWN - (now - db.get_last_card_time(uid)))} сек.")
        return

    target = db.get_random_user()
    if not target: 
        await message.reply("База гравців порожня!"); return
    tid, tname = target

    # Визначаємо випадкову рідкість
    import random
    r = random.random()
    if tid == MY_ID: rarity, bonus = "🛠 УНІКАЛЬНА (Розробник)", 100
    elif r < 0.05: rarity, bonus = "🟡 ЛЕГЕНДАРНА", 50
    elif r < 0.15: rarity, bonus = "🟣 ЕПІЧНА", 30
    elif r < 0.40: rarity, bonus = "🔵 РІДКІСНА", 15
    else: rarity, bonus = "⚪️ ЗВИЧАЙНА", 5

    db.add_coins(uid, bonus)
    db.add_to_collection(uid, tid, rarity)
    db.set_last_card_time(uid, now)

    # Фікс для аватарки
    photo = "https://i.imgur.com/KzS6CqC.png"
    try:
        p_photos = await bot.get_user_profile_photos(tid, limit=1)
        if p_photos.total_count > 0:
            photo = p_photos.photos[0][-1].file_id
    except: pass 

    caption = f"🌟 **Нова картка: {tname}**\n✨ Рідкість: {rarity}\n💰 Твій бонус: +{bonus} монет"
    await message.answer_photo(photo, caption=caption, parse_mode="Markdown")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
