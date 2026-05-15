import telebot
import sqlite3
import os
import json
from datetime import datetime, timedelta
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

def get_current_date():
    return datetime.now() + timedelta(days=-730)

class MessageState(Enum):
    MENU = auto()
    BRAND = auto()
    SUBJECT = auto()
    STAGE = auto()
    TURN = auto()
    CLASS = auto()
    CARD = auto()
    ADD = auto()
    DELETE = auto()
    SUBSCRIBE = auto()

@dataclass
class CallbackData:
    state: MessageState
    entity_id: Optional[int] = None
    timer: Optional[int] = None
    page: Optional[int] = None
    def serialize(self) -> str:
        return json.dumps({
            "s": self.state.name,
            "id": self.entity_id,
            "t": self.timer,
            "p": self.page
        })
    
    @classmethod
    def deserialize(cls, data: str) -> "CallbackData":
        try:
            parsed = json.loads(data)
            return cls(
                state=MessageState[parsed["s"]],
                entity_id=parsed.get("id"),
                timer=parsed.get("t"),
                page=parsed.get("p")
            )
        except (KeyError) as e:
            print(f"Ошибка десериализации callback: {e}")
            raise

def get_db_connection():
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

def create_callback_button(text: str, state: MessageState,
                           entity_id: int = None, timer: int = None, page: int = None) -> InlineKeyboardButton:
    callback = CallbackData(state=state, entity_id=entity_id, timer=timer, page=page)
    return InlineKeyboardButton(text, callback_data=callback.serialize())

def create_back_button(target_state: MessageState = MessageState.MENU) -> InlineKeyboardButton:
    return create_callback_button("Назад в меню", target_state)

def safe_db_query(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return results
    except sqlite3.Error as e:
        print(f"Ошибка БД: {e}")
        return []
    
@bot.message_handler(commands=["start"])
def hello_message(message):
    query = """
            INSERT INTO tg_User (user_id)
            VALUES (?)
            """
    safe_db_query(query, (message.from_user.id,))
    
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
    handle_menu_state(message.from_user.id, message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    bot.answer_callback_query(call.id)
    try:
        callback = CallbackData.deserialize(call.data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return

    id = call.message.chat.id
    user_id = call.message.from_user.id
    match callback.state:
        case MessageState.MENU:
            handle_menu_state(user_id, id, callback)
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
            handle_card_state(call, callback)
        case MessageState.ADD:
            if callback.timer is None:
                handle_add_state(call, callback)
            else:
                handle_add_final(call, callback)
        case MessageState.DELETE:
            if callback.timer is None:
                handle_delete_state(call, callback)
            else:
                handle_delete_final(call, callback)
        case MessageState.SUBSCRIBE:
            handle_my_subscriptions(call, callback)
            

def handle_menu_state(user_id, id, callback: CallbackData = None):
    menu_text = (
        "Здесь вы можете найти интересующую вас олимпиаду, "
        "либо управлять сделанными вами подписками (в разработке)."
    )
    keyboard = InlineKeyboardMarkup()
    subscribe_button = create_callback_button("Посмотреть свои олимпиады", MessageState.SUBSCRIBE)
    olimpiads_button = create_callback_button("Выбрать олимпиаду", MessageState.BRAND)
    keyboard.add(olimpiads_button, subscribe_button)
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

    keyboard = InlineKeyboardMarkup()

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
    keyboard = InlineKeyboardMarkup()

    current_year = datetime.now().year
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
    keyboard = InlineKeyboardMarkup()

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
    keyboard = InlineKeyboardMarkup()

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

def handle_card_state(call, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(call.message.chat.id, "Ошибка: не выбран класс участия.")
        return
    keyboard = InlineKeyboardMarkup()

    end_text = (
        "Выбор завершён!\n\n"
        "К сожалению, разработчики не добавили ничего про эту олимпиаду.\n"
        "Вы можете вернуться в главное меню."
    )

    query1 = """
            SELECT EXISTS
            (SELECT reminder_id FROM Reminder
            JOIN date ON date.date_id = Reminder.date_id
            JOIN tg_User ON tg_User.tg_user_id = Reminder.tg_user_id
            WHERE date.class_id = ? AND tg_user.user_id = ?)"""
    query2 = "SELECT date_id FROM date JOIN class ON date.class_id = ?"
    
    exists = safe_db_query(query1, (callback.entity_id, call.from_user.id))[0][0]
    date = safe_db_query(query2, (callback.entity_id,))[0]
    add_button = create_callback_button("Добавить напоминалку на эту олимпиаду", 
                                        MessageState.ADD, date["date_id"])
    keyboard.add(add_button)
    if (exists):
        delete_button = create_callback_button("Удалить напоминалку",
                                               MessageState.DELETE, date[0])
        keyboard.add(delete_button)

    keyboard.add(create_back_button(MessageState.MENU))

    bot.send_message(call.message.chat.id, text=end_text, reply_markup=keyboard)

def handle_add_state(call, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(call.message.chat.id, "Ошибка: не выбрана дата олимпиады.")
        return

    date_id = callback.entity_id
    user_id = call.from_user.id

    tg_user = safe_db_query(
        "SELECT tg_user_id FROM tg_User WHERE user_id = ?",
        (user_id,)
    )
    if not tg_user:
        bot.send_message(call.message.chat.id, "Вы не зарегистрированы. Напишите /start")
        return
    tg_user_id = tg_user[0]['tg_user_id']

    date = safe_db_query(
        "SELECT date FROM date WHERE date_id = ?",
        (date_id,)
    )
    if not date:
        bot.send_message(call.message.chat.id, "Ошибка: дата олимпиады не найдена.")
        return
    event_date = datetime.strptime(date[0]['date'], "%Y-%m-%d %H:%M:%S")

    options = [
        (1, "За день"),
        (7, "За неделю"),
        (30, "За месяц")
    ]

    keyboard = InlineKeyboardMarkup()
    for days, label in options:
        remind_date = event_date - timedelta(days=days)
        now = get_current_date()

        if remind_date <= now:
            continue

        existing = safe_db_query(
            "SELECT reminder_id FROM Reminder WHERE tg_user_id = ? AND date_id = ? AND timer = ?",
            (tg_user_id, date_id, days)
        )
        if existing:
            continue

        btn = create_callback_button(
            text=label,
            state=MessageState.ADD,
            entity_id=date_id,
            timer=days
        )
        keyboard.add(btn)

    if not keyboard.keyboard:
        bot.send_message(
            call.message.chat.id,
            "Нет доступных вариантов напоминания (либо все даты уже прошли, либо вы уже подписаны на все возможные таймеры)."
        )
        return

    keyboard.add(create_back_button(MessageState.MENU))
    bot.send_message(
        call.message.chat.id,
        "Выберите, за сколько дней до олимпиады вы хотите получить напоминание:",
        reply_markup=keyboard
    )


def handle_add_final(call, callback: CallbackData):
    if callback.entity_id is None or callback.timer is None:
        bot.send_message(call.message.chat.id, "Ошибка: не хватает данных для создания напоминания.")
        return

    date_id = callback.entity_id
    days = callback.timer
    user_id = call.from_user.id

    tg_user = safe_db_query(
        "SELECT tg_user_id FROM tg_User WHERE user_id = ?",
        (user_id,)
    )
    if not tg_user:
        bot.send_message(call.message.chat.id, "Ошибка регистрации. Напишите /start")
        return
    tg_user_id = tg_user[0]['tg_user_id']

    date = safe_db_query(
        "SELECT date FROM date WHERE date_id = ?",
        (date_id,)
    )
    if not date:
        bot.send_message(call.message.chat.id, "Дата олимпиады не найдена.")
        return
    event_date = datetime.strptime(date[0]['date'], "%Y-%m-%d %H:%M:%S")
    remind_date = event_date - timedelta(days=days)

    if remind_date <= get_current_date():
        bot.send_message(call.message.chat.id, "Дата отправки напоминания уже прошла. Нельзя добавить.")
        return

    existing = safe_db_query(
        "SELECT reminder_id FROM Reminder WHERE tg_user_id = ? AND date_id = ? AND timer = ?",
        (tg_user_id, date_id, days)
    )
    if existing:
        bot.send_message(call.message.chat.id, "Такое напоминание уже существует.")
        return
    
    do_it = safe_db_query(
        "INSERT INTO Reminder (tg_user_id, date_id, timer) VALUES (?, ?, ?)",
        (tg_user_id, date_id, days)
    )

    bot.send_message(
        call.message.chat.id,
        f"Напоминание добавлено! Вы получите уведомление за {days} день(дней) до олимпиады."
    )

def handle_delete_state(call, callback: CallbackData):
    if callback.entity_id is None:
        bot.send_message(call.message.chat.id, "Ошибка: не указана дата.")
        return

    date_id = callback.entity_id
    user_id = call.from_user.id

    tg_user = safe_db_query(
        "SELECT tg_user_id FROM tg_User WHERE user_id = ?",
        (user_id,)
    )
    if not tg_user:
        bot.send_message(call.message.chat.id, "Ошибка: пользователь не найден.")
        return
    tg_user_id = tg_user[0]['tg_user_id']

    reminders = safe_db_query(
        "SELECT timer FROM Reminder WHERE tg_user_id = ? AND date_id = ?",
        (tg_user_id, date_id)
    )
    if not reminders:
        bot.send_message(call.message.chat.id, "У вас нет напоминаний на эту дату.")
        return

    timer_names = {1: "За день", 7: "За неделю", 30: "За месяц"}

    keyboard = InlineKeyboardMarkup()
    for row in reminders:
        timer = row['timer']
        name = timer_names.get(timer, f"за {timer} дней")
        btn = create_callback_button(
            text=f"Удаляем {name}",
            state=MessageState.DELETE,
            entity_id=date_id,
            timer=timer
        )
        keyboard.add(btn)

    keyboard.add(create_back_button(MessageState.MENU))
    bot.send_message(
        call.message.chat.id,
        "Выберите напоминание для удаления:",
        reply_markup=keyboard
    )

def handle_delete_final(call, callback: CallbackData):
    if callback.entity_id is None or callback.timer is None:
        bot.send_message(call.message.chat.id, "Ошибка: не хватает данных для удаления.")
        return

    date_id = callback.entity_id
    days = callback.timer
    user_id = call.from_user.id

    tg_user = safe_db_query(
        "SELECT tg_user_id FROM tg_User WHERE user_id = ?",
        (user_id,)
    )
    if not tg_user:
        bot.send_message(call.message.chat.id, "Ошибка: пользователь не найден.")
        return
    tg_user_id = tg_user[0]['tg_user_id']

    do_it = safe_db_query(
        "DELETE FROM Reminder WHERE tg_user_id = ? AND date_id = ? AND timer = ?",
        (tg_user_id, date_id, days)
    )

    timer_names = {1: "за день", 7: "за неделю", 30: "за месяц"}
    name = timer_names.get(days, f"за {days} дней")
    bot.send_message(call.message.chat.id, f"Напоминание {name} удалено.")

def handle_my_subscriptions(call, callback: CallbackData):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    page = callback.page if callback.page is not None else 0
    items_per_page = 3

    tg_user_row = safe_db_query(
        "SELECT tg_user_id FROM tg_User WHERE user_id = ?",
        (user_id,)
    )
    if not tg_user_row:
        bot.send_message(chat_id, "Вы не зарегистрированы. Напишите /start")
        return
    tg_user_id = tg_user_row[0]['tg_user_id']

    query = """
        SELECT 
            r.reminder_id,
            r.timer,
            r.date_id,
            d.date as event_date,
            c.class_name,
            t.turn_name,
            s.stage_name,
            subj.subject_name,
            b.brand_name
        FROM Reminder r
        JOIN date d ON r.date_id = d.date_id
        JOIN class c ON d.class_id = c.class_id
        JOIN turn t ON c.turn_id = t.turn_id
        JOIN stage s ON t.stage_id = s.stage_id
        JOIN season sea ON s.season_id = sea.season_id
        JOIN subject subj ON sea.subject_id = subj.subject_id
        JOIN brand b ON subj.brand_id = b.brand_id
        WHERE r.tg_user_id = ?
        ORDER BY d.date ASC
    """
    all_reminders = safe_db_query(query, (tg_user_id,))
    total = len(all_reminders)

    if total == 0:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(create_back_button(MessageState.MENU))
        bot.send_message(chat_id, "У вас пока нет ни одной подписки.", reply_markup=keyboard)
        return

    start = page * items_per_page
    end = start + items_per_page
    reminders_page = all_reminders[start:end]
    total_pages = (total + items_per_page - 1) // items_per_page

    timer_names = {1: "за день", 7: "за неделю", 30: "за месяц"}
    message_lines = [f"*Ваши подписки* (страница {page+1} из {total_pages}):\n"]
    for idx, rem in enumerate(reminders_page, start=start+1):
        timer_text = timer_names.get(rem['timer'], f"за {rem['timer']} дней")
        message_lines.append(
            f"{idx}. *{rem['brand_name']}* — {rem['subject_name']}\n"
            f"   {rem['stage_name']} | {rem['turn_name']} | {rem['class_name']}\n"
            f"   Дата: {rem['event_date']}\n"
            f"   Напоминание: {timer_text}\n"
        )
    text = "\n".join(message_lines)

    keyboard = InlineKeyboardMarkup(row_width=2)
    for rem in reminders_page:
        btn = create_callback_button(
            text=f"Удалить [{timer_names.get(rem['timer'], rem['timer'])}]",
            state=MessageState.DELETE,
            entity_id=rem['date_id'],
            timer=rem['timer'],
            page=page
        )
        keyboard.add(btn)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(create_callback_button("Назад", MessageState.SUBSCRIBE, page=page-1))
    if page + 1 < total_pages:
        nav_buttons.append(create_callback_button("Вперёд", MessageState.SUBSCRIBE, page=page+1))
    if nav_buttons:
        keyboard.row(*nav_buttons)

    keyboard.add(create_back_button(MessageState.MENU))

    try:
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="Markdown")

bot.infinity_polling()