import asyncio
import time
import threading
import random
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import Database

# Сервер для Render
app = Flask('')
@app.route('/')
def home(): return "Привіт!"
def run(): app.run(host='0.0.0.0', port=10000)
def keep_alive():
    t = threading.Thread(target=run); t.daemon = True; t.start()

# --- КОНФІГУРАЦІЯ ---
TOKEN = "8161816299:AAG_x1WArl0oQviMYF77UChNJJ4uygdH7YM"
MY_ID = 7518373450 
DB_URL = "postgresql://sajmastudio_user:rO7AUee4Nw5glwSAynGNhq2DSycDbkDx@dpg-d7stl1beo5us73eqma5g-a.oregon-postgres.render.com/sajmastudio"
COOLDOWN = 60

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = Database(DB_URL)

# --- КЛАВІАТУРИ ---
def get_main_keyboard(user_id):
    buttons = [
        [KeyboardButton(text="Картка"), KeyboardButton(text="Профіль")],
        [KeyboardButton(text="Кейси"), KeyboardButton(text="ТОП")]
    ]
    if user_id == MY_ID:
        buttons.append([KeyboardButton(text="Адмін-меню")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cases_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚪️ Звичайний (50 💰)"), KeyboardButton(text="🔵 Рідкісний (150 💰)")],
            [KeyboardButton(text="Назад")]
        ], resize_keyboard=True
    )

# --- ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db.update_user(message.from_user.id, message.from_user.full_name)
    await message.answer("Sajma Studio вітає тебе! Обирай дію:", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(F.text == "Профіль")
async def show_profile(message: types.Message):
    uid = message.from_user.id
    coins, msgs = db.get_user_data(uid)
    collected = db.get_total_collected(uid)
    total_in_db = db.get_total_players()
    stats = db.get_user_collection_stats(uid)
    
    text = (
        f"👤 **Профіль: {message.from_user.full_name}**\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"💰 Баланс: `{coins}`\n"
        f"✉️ Повідомлень: `{msgs}`\n"
        f"🃏 Колекція: `{collected}/{total_in_db}`\n\n"
        f"✨ **Рідкості:**\n"
        f"⚪️ Звичайні: `{stats.get('⚪️ ЗВИЧАЙНА', 0)}` | 🔵 Рідкісні: `{stats.get('🔵 РІДКІСНА', 0)}`\n"
        f"🟣 Епічні: `{stats.get('🟣 ЕПІЧНА', 0)}` | 🟡 Легендарні: `{stats.get('🟡 ЛЕГЕНДАРНА', 0)}`"
    )
    await message.reply(text, parse_mode="Markdown")

@dp.message(F.text == "ТОП")
async def show_top(message: types.Message):
    top_list = db.get_top_rich(limit=10) # Додай цей метод в БД
    if not top_list: return await message.answer("🏆 Список порожній!")
    
    text = "🏆 **ТОП-10 БАГАТІЇВ:**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    for i, (name, balance) in enumerate(top_list, 1):
        icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
        text += f"{icon} {i}. {name} — `{balance}` 💰\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "Картка")
async def give_card_handler(message: types.Message):
    await get_card(message)

@dp.message(F.text == "Кейси")
async def cases_menu(message: types.Message):
    await message.answer("Оберіть кейс для відкриття:", reply_markup=get_cases_keyboard())

@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    await message.answer("Повертаємось...", reply_markup=get_main_keyboard(message.from_user.id))

# --- АДМІН ПАНЕЛЬ ---
@dp.message(F.text == "🛠 Адмін-меню")
async def admin_panel(message: types.Message):
    if message.from_user.id != MY_ID: return
    text = (
        "🛠 **АДМІН-КЕРУВАННЯ**\n\n"
        "`додати ID Ім'я` — додати в базу\n"
        "`очистити ID` — скинути профіль\n"
        "`видати_монети ID сума` — бонус гравцю"
    )
    await message.answer(text, parse_mode="Markdown")

# Додай обробку видачі монет в handle_msg...

async def get_card(message: types.Message):
    uid = message.from_user.id
    now = time.time()
    
    if uid != MY_ID and (now - db.get_last_card_time(uid) < COOLDOWN):
        wait = int(COOLDOWN - (now - db.get_last_card_time(uid)))
        return await message.reply(f"⏳ Зачекай ще {wait} сек.")

    target = db.get_random_user()
    if not target: return await message.answer("📭 База порожня!")
    tid, tname = target

    r = random.random()
    if tid == MY_ID: rarity, bonus = "🛠 УНІКАЛЬНА", 100
    elif r < 0.05: rarity, bonus = "🟡 ЛЕГЕНДАРНА", 50
    elif r < 0.15: rarity, bonus = "🟣 ЕПІЧНА", 30
    elif r < 0.40: rarity, bonus = "🔵 РІДКІСНА", 15
    else: rarity, bonus = "⚪️ ЗВИЧАЙНА", 5

    db.add_coins(uid, bonus)
    db.add_to_collection(uid, tid, rarity)
    db.set_last_card_time(uid, now)

    photo = "https://i.imgur.com/KzS6CqC.png"
    try:
        p_photos = await bot.get_user_profile_photos(tid, limit=1)
        if p_photos.total_count > 0:
            photo = p_photos.photos[0][-1].file_id
    except: pass 

    caption = f"🃏 **Знайдено картку: {tname}**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n✨ Рідкість: {rarity}\n💰 Бонус: +{bonus} монет"
    await message.answer_photo(photo, caption=caption, parse_mode="Markdown")

# Обов'язково додаємо підрахунок повідомлень
@dp.message()
async def global_handler(message: types.Message):
    if not message.text or message.text.startswith('/'): return
    db.update_user(message.from_user.id, message.from_user.full_name)

async def main():
    keep_alive()
    print("Привіт")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
