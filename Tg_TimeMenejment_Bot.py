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
