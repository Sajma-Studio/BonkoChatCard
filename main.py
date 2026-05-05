import asyncio
import time
import threading
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import Database

# --- СЕРВЕР ДЛЯ RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Sajma Studio Bot is alive!"

def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --- НАЛАШТУВАННЯ ---
TOKEN = "8161816299:AAG_x1WArl0oQviMYF77UChNJJ4uygdH7YM"
MY_ID = 7518373450  # Макс (Розробник)
OWNER_ID = 6810492221
COOLDOWN = 60

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database("db.sqlite")

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🃏 Картка"), KeyboardButton(text="👤 Профіль")]],
        resize_keyboard=True,
        input_field_placeholder="Обери дію..."
    )
    return keyboard

# --- ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Тисни на кнопки, щоб грати.", reply_markup=get_main_keyboard())

@dp.message(F.text)
async def handle_msg(message: types.Message):
    # АДМІН-КОМАНДА: додати ID Ім'я
    if message.from_user.id == MY_ID and message.text.startswith("додати"):
        try:
            parts = message.text.split(" ", 2)
            db.manual_add_user(int(parts[1]), parts[2])
            await message.reply(f"✅ Додано: {parts[2]} ({parts[1]})")
        except:
            await message.reply("Формат: `додати 123456 Ім'я`")
        return

    # КНОПКИ
    if message.text == "🃏 Картка":
        await get_card(message)
    elif message.text == "👤 Профіль":
        coins, msgs = db.get_user_data(message.from_user.id)
        total_players = db.get_user_stats()
        text = (
            f"👤 **Твій профіль:**\n\n"
            f"💰 Баланс: `{coins}` монет\n"
            f"✉️ Повідомлень: `{msgs}`\n"
            f"🃏 Зібрано карток: `0/{total_players}`\n\n"
            f"✨ **Колекція:**\n"
            f"⚪️ Звичайні: `0` | 🔵 Рідкісні: `0` | 🟣 Епічні: `0` | 🟡 Лег: `0`"
        )
        await message.reply(text, parse_mode="Markdown")
    
    # Реєстрація активності
    if not message.text.startswith('/'):
        db.update_user(message.from_user.id, message.from_user.full_name)

async def get_card(message: types.Message):
    user_id = message.from_user.id
    now = time.time()
    if now - db.get_last_card_time(user_id) < COOLDOWN:
        await message.reply(f"⏳ Зачекай {int(COOLDOWN - (now - db.get_last_card_time(user_id)))} сек.!")
        return

    target = db.get_random_user()
    if not target:
        await message.reply("База порожня!"); return

    tid, tname = target
    if tid == MY_ID: rarity, bonus = "🛠 УНІКАЛЬНА (Розробник)", 100
    elif tid == OWNER_ID: rarity, bonus = "👑 КОРОЛІВСЬКА (Власник)", 100
    else: rarity, bonus = db.get_rarity_info(tid)

    db.add_coins(user_id, bonus)
    db.set_last_card_time(user_id, now)
    
    try:
        photos = await bot.get_user_profile_photos(tid, limit=1)
        photo = photos.photos[0][-1].file_id if photos.total_count > 0 else "https://i.imgur.com/KzS6CqC.png"
    except: photo = "https://i.imgur.com/KzS6CqC.png"

    caption = f"🌟 **Картка: {tname}**\n✨ Рідкість: {rarity}\n💰 Бонус: +{bonus} монет"
    await message.answer_photo(photo, caption=caption, parse_mode="Markdown")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
