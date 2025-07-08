from dotenv import load_dotenv
import os
load_dotenv()
TOKEN = os.getenv('TOKEN')
import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
import random


TZ = "Europe/Moscow" 
DATA_FILE = "data.json" 


CATEGORIES = {
    "workout": {"emoji": "💪", "prefix": "Самое время на тренировку!"},
    "birthday": {"emoji": "🎂", "prefix": "Сегодня день рождения у"},
    "default": {"emoji": "⏰", "prefix": ""}
}


SUCCESS_GIFS = ["https://media.giphy.com/media/1.gif  ", "https://media.giphy.com/media/2.gif  "]
FAIL_GIFS = ["https://media.giphy.com/media/3.gif  ", "https://media.giphy.com/media/4.gif  "]


reminders = {}  
stats = {} 
user_tags = {}  
user_states = {}  

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TZ)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏋️ Статистика")],
        [KeyboardButton(text="➕ Новое напоминание")],
        [KeyboardButton(text="🏷️ Теги")],
        [KeyboardButton(text="🔔 Мои уведомления")]
    ],
    resize_keyboard=True
)

def load_data():
    global reminders, stats, user_tags
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                reminders = {int(k): v for k, v in data.get("reminders", {}).items()}
                stats = {int(k): v for k, v in data.get("stats", {}).items()}
                user_tags = {int(k): v for k, v in data.get("user_tags", {}).items()}
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")

def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({
                "reminders": reminders,
                "stats": stats,
                "user_tags": user_tags
            }, f, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")

@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in reminders:
        reminders[user_id] = []
        stats[user_id] = {"workout_count": 0, "total_tasks": 0}
        user_tags[user_id] = {}
    await message.reply("Привет! Добавьте напоминание:\n`workout 15:00 Выпить воды`", parse_mode="Markdown",
                        reply_markup=main_menu)

@dp.message(lambda m: m.text == "🏋️ Статистика")
@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    user_id = message.from_user.id
    data = stats.get(user_id, {"workout_count": 0, "total_tasks": 0})
    await message.reply(f"🏋️ Тренировок выполнено: {data['workout_count']}\n"
                        f"📊 Всего задач: {data['total_tasks']}")

@dp.message(lambda m: m.text == "🏷️ Теги")
@dp.message(Command("new_signal"))
async def manage_tags(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = "manage_tags"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="📚 Системные теги", callback_data="system_tags")
    ])
    for tag in CATEGORIES:
        if tag != "default":
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"🏷️ {tag}", callback_data=f"system_tag_{tag}")
            ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🧩 Пользовательские теги", callback_data="user_tags")
    ])
    for tag in user_tags.get(user_id, {}):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"🏷️ {tag}", callback_data=f"edit_tag_{tag}")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="➕ Новый тег", callback_data="add_tag")
    ])
    
    await message.reply("Управление тегами:\n\nВыберите тег для просмотра или создайте новый:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "add_tag")
async def add_new_tag(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_states[user_id] = "waiting_for_tag_name"
    await callback.message.edit_text("Введите имя для нового тега:")

@dp.callback_query(lambda c: c.data.startswith("edit_tag_"))
async def edit_tag(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tag_name = callback.data.split("_")[2]
    user_states[user_id] = f"editing_tag_{tag_name}"
    current_text = user_tags[user_id].get(tag_name, "")
    await callback.message.edit_text(f"Текущий текст для '{tag_name}': {current_text}\n\nВведите новый текст:")

@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if user_states.get(user_id) == "waiting_for_tag_name":
        user_states[user_id] = f"waiting_for_tag_text_{text}"
        await message.reply(f"Введите текст для тега '{text}':")
        return
    
    elif user_states.get(user_id, "").startswith("waiting_for_tag_text_"):
        tag_name = user_states[user_id].replace("waiting_for_tag_text_", "")
        if user_id not in user_tags:
            user_tags[user_id] = {}
        user_tags[user_id][tag_name] = text
        user_states.pop(user_id, None)
        save_data()
        await message.reply(f"✅ Тег '{tag_name}' создан!")
        await manage_tags(message)
        return
    
    elif user_states.get(user_id, "").startswith("editing_tag_"):
        tag_name = user_states[user_id].replace("editing_tag_", "")
        user_tags[user_id][tag_name] = text
        user_states.pop(user_id, None)
        save_data()
        await message.reply(f"✅ Тег '{tag_name}' обновлен!")
        await manage_tags(message)
        return
    
    if user_states.get(user_id) == "adding_reminder":
        user_states.pop(user_id, None)
        parts = text.split()
        if not parts:
            return
            
        category = parts[0]
        if category in CATEGORIES or category in user_tags.get(user_id, {}):
            system_tags = "\n".join([f"🏷️ {tag}" for tag in CATEGORIES if tag != "default"])
            user_tag_list = user_tags.get(user_id, {})
            user_tags_str = "\n".join([f"🏷️ {tag}" for tag in user_tag_list]) if user_tag_list else "Нет пользовательских тегов"
            
            await message.reply(
                f"Доступные теги:\n"
                f"Системные:\n{system_tags}\n"
                f"Пользовательские:\n{user_tags_str}\n\n"
                f"Введите напоминание в формате:\n"
                f"[категория/тег] [время] [текст]\n"
                f"Пример:\n"
                f"{category} 15:00 Выпить воды"
            )
            return
    
    parts = text.split()
    if not parts:
        return
    
    if parts[0] in CATEGORIES or parts[0] in user_tags.get(user_id, {}):
        category = parts[0]
        reminder_text = " ".join(parts[1:])
        
        system_tags = "\n".join([f"🏷️ {tag}" for tag in CATEGORIES if tag != "default"])
        user_tag_list = user_tags.get(user_id, {})
        user_tags_str = "\n".join([f"🏷️ {tag}" for tag in user_tag_list]) if user_tag_list else "Нет пользовательских тегов"
        
        await message.reply(
            f"Доступные теги:\n"
            f"Системные:\n{system_tags}\n"
            f"Пользовательские:\n{user_tags_str}\n\n"
            f"Введите напоминание в формате:\n"
            f"[категория/тег] [время] [текст]\n\n"
            f"Пример для {category}:\n"
            f"{category} 15:00 Выпить воды"
        )
        return
    
    await message.reply("Неизвестная команда. Используйте главное меню.")

@dp.message(lambda m: m.text == "➕ Новое напоминание")
async def new_reminder_prompt(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = "adding_reminder"
    
    system_tags = "\n".join([f"🏷️ {tag}" for tag in CATEGORIES if tag != "default"])
    user_tag_list = user_tags.get(user_id, {})
    user_tags_str = "\n".join([f"🏷️ {tag}" for tag in user_tag_list]) if user_tag_list else "Нет пользовательских тегов"
    
    await message.reply(
        f"Введите напоминание в формате:\n"
        f"[категория/тег] [время] [текст]\n\n"
        f"Доступные теги:\n"
        f"Системные:\n{system_tags}\n"
        f"Пользовательские:\n{user_tags_str}",
        parse_mode="Markdown"
    )

async def send_reminder(user_id, text, category):
    emoji = CATEGORIES.get(category, {}).get("emoji", "⏰")
    prefix = CATEGORIES.get(category, {}).get("prefix", "")
    
    if category in user_tags.get(user_id, {}):
        prefix = ""
        text = user_tags[user_id][category]
        
    message = f"{emoji} {prefix} {text}" if prefix else f"{emoji} {text}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"complete_{user_id}_{category}_{text}")]
    ])
    
    try:
        await bot.send_message(user_id, message, reply_markup=keyboard)
        await bot.send_animation(user_id, animation=random.choice(SUCCESS_GIFS))
    except Exception as e:
        print(f"Ошибка отправки пользователю {user_id}: {e}")

@dp.callback_query()
async def handle_complete(callback: types.CallbackQuery):
    data = callback.data.split("_")
    if data[0] == "complete":
        user_id = int(data[1])
        category = data[2]
        text = "_".join(data[3:]) 
        
        if category == "workout":
            stats[user_id]["workout_count"] += 1
        stats[user_id]["total_tasks"] += 1
        save_data()
        
        await callback.message.edit_text(f"✅ Вы успешно отметили выполнение: {text}")
        await bot.send_animation(user_id, animation=random.choice(SUCCESS_GIFS))

@dp.message(lambda m: m.text == "🔔 Мои уведомления")
@dp.message(Command("my_reminders"))
async def my_reminders(message: types.Message):
    user_id = message.from_user.id
    user_reminders = reminders.get(user_id, [])
    
    if not user_reminders:
        await message.reply("У вас нет активных напоминаний.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for idx, reminder in enumerate(user_reminders):
        time_str = reminder.get("time", "")
        text = reminder.get("text", "")
        category = reminder.get("category", "")
        date_str = reminder.get("date", "")
        
        if category == "birthday" and date_str:
            display = f"{CATEGORIES.get(category, {}).get('emoji', '⏰')} {date_str} {time_str} - {text}"
        elif category in CATEGORIES:
            display = f"{CATEGORIES.get(category, {}).get('emoji', '⏰')} {time_str} - {text}"
        else:
            display = f"⏰ {time_str} - {text}"
            
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=display, callback_data=f"delete_reminder_{idx}")
        ])
    
    await message.reply("Ваши напоминания:", reply_markup=keyboard)

@dp.callback_query()
async def handle_delete_reminder(callback: types.CallbackQuery):
    data = callback.data.split("_")
    if data[0] == "delete":
        user_id = callback.from_user.id
        try:
            idx = int(data[2])
            if 0 <= idx < len(reminders.get(user_id, [])):
                removed = reminders[user_id].pop(idx)
                save_data()
                await callback.message.edit_text(f"🗑 Удалено напоминание: {removed['text']}")
        except (ValueError, IndexError):
            pass
            
async def main():
    load_data() 
    
    for user_id, user_reminders in reminders.items():
        for reminder in user_reminders:
            category = reminder.get("category")
            time_str = reminder.get("time", "00:00")
            
            try:
                hour, minute = map(int, time_str.split(":"))
                
                if category == "birthday":
                    date_str = reminder.get("date", "01.01")
                    day, month = map(int, date_str.split("."))
                    scheduler.add_job(
                        send_reminder,
                        "cron",
                        day=day,
                        month=month,
                        hour=hour,
                        minute=minute,
                        args=[user_id, reminder["text"], category]
                    )
                else:
                    scheduler.add_job(
                        send_reminder,
                        "cron",
                        hour=hour,
                        minute=minute,
                        args=[user_id, reminder["text"], category]
                    )
            except Exception as e:
                print(f"Ошибка восстановления напоминания: {e}")
    
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        save_data() 
