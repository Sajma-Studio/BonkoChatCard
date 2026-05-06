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
def home(): return "Sajma Studio Bot is alive!"
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
        [KeyboardButton(text="🃏 Картка"), KeyboardButton(text="👤 Профіль")],
        [KeyboardButton(text="🎁 Кейси"), KeyboardButton(text="🏆 ТОП")]
    ]
    if user_id == MY_ID:
        buttons.append([KeyboardButton(text="🛠 Адмін-меню"), KeyboardButton(text="📊 База")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_cases_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚪️ Звичайний (50 💰)"), KeyboardButton(text="🔵 Рідкісний (150 💰)")],
            [KeyboardButton(text="⬅️ Назад")]
        ], resize_keyboard=True
    )

# --- ФУНКЦІЯ ВИДАЧІ КАРТКИ ---
async def open_case(message, cost, is_rare=False):
    uid = message.from_user.id
    if db.take_coins(uid, cost):
        target = db.get_random_user()
        if not target: return
        tid, tname = target

        # Шанси для кейсів
        r = random.random()
        if is_rare: # Рідкісний кейс: мінімум Рідкісна
            if r < 0.20: rarity, bonus = "🟡 ЛЕГЕНДАРНА", 100
            elif r < 0.50: rarity, bonus = "🟣 ЕПІЧНА", 60
            else: rarity, bonus = "🔵 РІДКІСНА", 30
        else: # Звичайний кейс
            if r < 0.05: rarity, bonus = "🟣 ЕПІЧНА", 40
            elif r < 0.20: rarity, bonus = "🔵 РІДКІСНА", 20
            else: rarity, bonus = "⚪️ ЗВИЧАЙНА", 10

        db.add_to_collection(uid, tid, rarity)
        await message.answer(f"🎁 Кейс відкрито!\n🃏 Випала картка: **{tname}**\n✨ Рідкість: {rarity}", parse_mode="Markdown")
    else:
        await message.answer("❌ Недостатньо монет!")

# --- ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db.update_user(message.from_user.id, message.from_user.full_name)
    await message.answer("Sajma Studio вітає тебе!", reply_markup=get_main_keyboard(message.from_user.id))

@dp.message(F.text == "📊 База")
async def show_base(message: types.Message):
    if message.from_user.id != MY_ID: return
    users = db.get_all_users()
    text = "📊 **Список всіх гравців:**\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    for uid, name, coins in users:
        text += f"• `{uid}` | {name} | {coins}💰\n"
    if len(text) > 4000: text = text[:4000] + "..." # Телеграм не пропустить довгі повідомлення
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🎁 Кейси")
async def cases_menu(message: types.Message):
    await message.answer("Оберіть кейс:", reply_markup=get_cases_keyboard())

@dp.message(F.text == "⚪️ Звичайний (50 💰)")
async def buy_common(message: types.Message):
    await open_case(message, 50, is_rare=False)

@dp.message(F.text == "🔵 Рідкісний (150 💰)")
async def buy_rare(message: types.Message):
    await open_case(message, 150, is_rare=True)

@dp.message(F.text == "🛠 Адмін-меню")
async def admin_panel(message: types.Message):
    if message.from_user.id != MY_ID: return
    await message.answer("🛠 Команди:\n`додати ID Ім'я`\n`очистити ID`\n`видати ID сума`", parse_mode="Markdown")

@dp.message(F.text)
async def handle_msg(message: types.Message):
    user_id = message.from_user.id
    
    # Виправлена адмін-логіка
    if user_id == MY_ID:
        parts = message.text.split()
        if parts[0] == "додати" and len(parts) >= 3:
            db.manual_add_user(int(parts[1]), " ".join(parts[2:]))
            return await message.reply("✅ Додано!")
        
        if parts[0] == "очистити" and len(parts) == 2:
            db.reset_user(int(parts[1]))
            return await message.reply("🧹 Очищено!")

        if parts[0] == "видати" and len(parts) == 3:
            db.add_coins(int(parts[1]), int(parts[2]))
            return await message.reply(f"💰 Видано {parts[2]} монет!")

    # Кнопки
    if message.text == "🃏 Картка":
        await get_card(message)
    elif message.text == "👤 Профіль":
        coins, msgs = db.get_user_data(user_id)
        collected = db.get_total_collected(user_id)
        total = db.get_total_players()
        stats = db.get_user_collection_stats(user_id)
        text = f"👤 **Профіль**\n💰 Баланс: `{coins}`\n🃏 Колекція: `{collected}/{total}`"
        await message.reply(text, parse_mode="Markdown")
    elif message.text == "🏆 ТОП":
        top = db.get_top_rich()
        text = "🏆 **ТОП-10 Багатіїв:**\n" + "\n".join([f"{i+1}. {u[0]} - {u[1]}💰" for i, u in enumerate(top)])
        await message.answer(text)
    elif message.text == "⬅️ Назад":
        await message.answer("Головне меню", reply_markup=get_main_keyboard(user_id))
    
    # Рахуємо повідомлення
    db.update_user(user_id, message.from_user.full_name)

async def get_card(message: types.Message):
    uid = message.from_user.id
    now = time.time()
    if uid != MY_ID and (now - db.get_last_card_time(uid) < COOLDOWN):
        return await message.reply(f"⏳ Зачекай {int(COOLDOWN - (now - db.get_last_card_time(uid)))} сек.")

    target = db.get_random_user()
    if not target: return
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

    # Фото
    photo = "https://i.imgur.com/KzS6CqC.png"
    try:
        p_photos = await bot.get_user_profile_photos(tid, limit=1)
        if p_photos.total_count > 0: photo = p_photos.photos[0][-1].file_id
    except: pass 
    
    await message.answer_photo(photo, caption=f"🃏 Картка: {tname}\n✨ Рідкість: {rarity}\n💰 +{bonus}")

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
