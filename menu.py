import telebot
import datetime
import sqlite3
import os
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple

load_dotenv()
bot_token = os.getenv("BOT_TOKEN")

if not bot_token:
    raise RuntimeError(
        "BOT_TOKEN не найден в переменных окружения!"
        "Проверьте .env файл или переменные среды."
    )

bot = telebot.TeleBot(bot_token)
db = "TEST_db.db"

class MessageState(Enum):
    MENU = auto()
    BRAND = auto()
    SUBJECT = auto()
    STAGE = auto()
    TURN = auto()
    CLASS = auto()
    CARD = auto()

@dataclass
class CallbackData:
    state: MessageState
    entity_id: Optional[int] = None

    def serialize(self) -> str:
        return json.dumps({
            "s": self.state.name,
            "id": self.entity_id
        })
    
    @classmethod
    def deserialize(cls, data: str) -> "CallbackData":
        try:
            parsed = json.loads(data)
            return cls(
                state=MessageState[parsed["s"]],
                entity_id=parsed.get("id")
            )
        except (KeyError) as e:
            print(f"Ошибка десериализации callback: {e}")
            raise

def get_db_connection():
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

def create_callback_button(text: str, state: MessageState, entity_id: int = None) -> InlineKeyboardButton:
    callback = CallbackData(state=state, entity_id=entity_id)
    return InlineKeyboardButton(text, callback_data=callback.serialize())

def create_back_button(target_state: MessageState = MessageState.MENU) -> InlineKeyboardButton:
    return create_callback_button("Назад в меню", target_state)

def safe_db_query(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except sqlite3.Error as e:
        print(f"Ошибка БД: {e}")
        return []
    
@bot.message_handler(commands=["start"])
def hello_message(message):
    start_text = (
        "Здравствуйте! Этот бот поможет вам не забыть про свои олимпиады.\n\n"
        "Он будет напоминать вам про начало именно ваших олимпиад.\n"
        "По кнопке ниже вы можете перейти в меню для настройки напоминаний.\n"
        "Также в меню можно попасть по команде /menu"
    )
    keyboard = InlineKeyboardMarkup()
    menu_button = create_callback_button("Главное меню", MessageState.MENU)
    keyboard.add(menu_button)

    bot.send_message(message.chat.id, text=start_text, reply_markup=keyboard)

@bot.message_handler(commands=["menu"])
def menu_command(message):
    handle_menu_state(message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    bot.answer_callback_query(call.id)
    try:
        callback = CallbackData.deserialize(call.data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return

    id = call.message.chat.id
    match callback.state:
        case MessageState.MENU:
            handle_menu_state(id, callback)
        case MessageState.BRAND:
            handle_brand_state(id, callback)
        case MessageState.SUBJECT:
            handle_subject_state(id, callback)
        case MessageState.STAGE:
            handle_stage_state(id, callback)
        case MessageState.TURN:
            handle_turn_state(id, callback)
        case MessageState.CLASS:
            handle_class_state(id, callback)
        case MessageState.CARD:
            handle_card_state(id, callback)

def handle_menu_state(id, callback: CallbackData = None):
    menu_text = (
        "Здесь вы можете найти интересующую вас олимпиаду, "
        "либо управлять сделанными вами подписками (в разработке)."
    )
    keyboard = InlineKeyboardMarkup()
    #subscribe_button
    olimpiads_button = create_callback_button("Выбрать олимпиаду", MessageState.BRAND)
    keyboard.add(olimpiads_button)
    bot.send_message(id, text=menu_text, reply_markup=keyboard)

def handle_brand_state(id, callback: CallbackData):
    keyboard = InlineKeyboardMarkup()

    brands = safe_db_query("SELECT brand_id, brand_name FROM brand")
    if not brands:
        bot.send_message(id, "Нет доступных олимпиад.")
        return
    
    for brand in brands:
        button = create_callback_button(
            text=brand['brand_name'],
            state=MessageState.SUBJECT,
            entity_id=brand['brand_id']
        )
        keyboard.add(button)
    keyboard.add(create_back_button())

    bot.send_message(id, "Выберите бренд олимпиады:", reply_markup=keyboard)

def handle_subject_state(id, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(id, "Ошибка: не выбран бренд.")
        return

    keyboard = InlineKeyboardMarkup(row_width=1)

    subjects = safe_db_query(
        "SELECT subject_id, subject_name FROM subject WHERE brand_id = ?",
        (callback.entity_id,)
    )

    if not subjects:
        bot.send_message(id, "Нет предметов для этой олимпиады.")
        return

    for subject in subjects:
        button = create_callback_button(
            text=subject['subject_name'],
            state=MessageState.STAGE,
            entity_id=subject['subject_id']
        )
        keyboard.add(button)

    keyboard.add(create_back_button(MessageState.MENU))

    bot.send_message(id, "Выберите предмет участия:", reply_markup=keyboard)

def handle_stage_state(id, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(id, "Ошибка: не выбран предмет.")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)

    current_year = datetime.datetime.now().year
    next_season = f"{current_year}/{current_year + 1}"
    prev_season = f"{current_year - 1}/{current_year}"

    query = """
        SELECT stage.stage_id, stage.stage_name
        FROM stage
        JOIN season ON stage.season_id = season.season_id
        WHERE season.subject_id = ?
          AND (season.season_name = ? OR season.season_name = ?)
    """
    stages = safe_db_query(query, (callback.entity_id, next_season, prev_season))

    if not stages:
        bot.send_message(id, "Нет доступных этапов.")
        return

    for stage in stages:
        button = create_callback_button(
            text=stage['stage_name'],
            state=MessageState.TURN,
            entity_id=stage['stage_id']
        )
        keyboard.add(button)

    keyboard.add(create_back_button(MessageState.MENU))

    bot.send_message(id, "Выберите этап олимпиады:", reply_markup=keyboard)

def handle_turn_state(id, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(id, "Ошибка: не выбран этап.")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)

    turns = safe_db_query(
        "SELECT turn_id, turn_name FROM turn WHERE stage_id = ?",
        (callback.entity_id,)
    )

    if not turns:
        bot.send_message(id, "Нет доступных туров.")
        return

    if len(turns) == 1:
        next_callback = CallbackData(
            state=MessageState.CLASS,
            entity_id=turns[0]['turn_id'],
        )
        handle_class_state(id, next_callback)
        return
    for turn in turns:
        button = create_callback_button(
            text=turn['turn_name'],
            state=MessageState.CLASS,
            entity_id=turn['turn_id']
        )
        keyboard.add(button)

    keyboard.add(create_back_button(MessageState.MENU))

    bot.send_message(id, "Выберите номер тура олимпиады:", reply_markup=keyboard)

def handle_class_state(id, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(id, "Ошибка: не выбран тур.")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)

    classes = safe_db_query(
        "SELECT class_id, class_name FROM class WHERE turn_id = ?",
        (callback.entity_id,)
    )

    if not classes:
        bot.send_message(id, "Нет доступных классов.")
        return
    
    for cls in classes:
        button = create_callback_button(
            text=cls['class_name'],
            state=MessageState.CARD,
            entity_id=cls['class_id']
        )
        keyboard.add(button)
    keyboard.add(create_back_button(MessageState.MENU))

    bot.send_message(id, "Выберите класс участия:", reply_markup=keyboard)

def handle_card_state(id, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(id, "Ошибка: не выбран класс участия.")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)

    end_text = (
        "✅ Выбор завершён!\n\n"
        "К сожалению, разработчики не добавили ничего про эту олимпиаду.\n"
        "Вы можете вернуться в главное меню."
    )

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(create_back_button(MessageState.MENU))

    bot.send_message(id, text=end_text, reply_markup=keyboard)

bot.infinity_polling()