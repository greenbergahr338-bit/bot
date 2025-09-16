import asyncio, os, csv, logging
from datetime import datetime
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# === НАСТРОЙКИ (вставлены прямо тут) ===
BOT_TOKEN       = ""
MANAGER_CHAT_ID = 7491118216
CHANNEL_LINK    = "https://t.me/+lbkzPyb0O1BmZDQy"
REVIEWS_LINK    = "https://t.me/CardUPreviews"
MANAGER_LINK    = "https://t.me/cardupp"
SITE_LINK       = "https://cardupof.ru"
LOG_FILE        = "leads.csv"

if not BOT_TOKEN or BOT_TOKEN.startswith("ВСТАВЬ"):
    raise SystemExit("❌ BOT_TOKEN пуст. Вставь его прямо в bot.py в переменную BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cardup-bot")

bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp  = Dispatcher()
r   = Router()
dp.include_router(r)

# === Состояния анкеты ===
class Lead(StatesGroup):
    flow = State()
    name = State()
    age  = State()
    tg   = State()

# === Клавиатуры ===
def kb_welcome():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать", callback_data="start_form")],
        [InlineKeyboardButton(text="📣 Канал", url=CHANNEL_LINK),
         InlineKeyboardButton(text="⭐ Отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="🌐 Сайт", url=SITE_LINK)]
    ])

def kb_finish():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📣 Подписаться на основной канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="⭐ Подписаться на отзывы", url=REVIEWS_LINK)],
        [InlineKeyboardButton(text="🌐 Открыть сайт", url=SITE_LINK)],
        [InlineKeyboardButton(text="👤 Связаться с менеджером", url=MANAGER_LINK)],
    ])

# === Утилиты ===
def clean(s: str) -> str: return (s or "").strip()

async def notify_manager(data: dict):
    if not MANAGER_CHAT_ID: return
    text = (
        "🆕 <b>Новая заявка</b>\n"
        f"Источник: <code>{data.get('flow','-')}</code>\n"
        f"Имя: <b>{data.get('name','-')}</b>\n"
        f"Возраст: <b>{data.get('age','-')}</b>\n"
        f"Telegram: <b>{data.get('tg','-')}</b>\n"
        f"User ID: <code>{data.get('user_id')}</code>\n"
        f"Дата: <code>{datetime.now().strftime('%d.%m.%Y %H:%M')}</code>"
    )
    try:
        await bot.send_message(MANAGER_CHAT_ID, text)
    except Exception as e:
        log.exception("send to manager failed: %s", e)

def save_csv(data: dict):
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        if new_file: w.writerow(["dt","user_id","flow","name","age","tg"])
        w.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get("user_id"), data.get("flow"),
            data.get("name"), data.get("age"), data.get("tg")
        ])

# === Старт ===
@r.message(CommandStart(deep_link=True))
async def start_deep(m: Message, state: FSMContext, command: CommandStart):
    payload = (command.args or "").lower().strip()
    flow = "card14" if payload == "card14" else ("card18" if payload == "card18" else "plain")
    await state.clear()
    await state.update_data(flow=flow, user_id=m.from_user.id)
    await m.answer(
        "Привет 👋 Это CardUP.\n\n"
        "Мы — официальный партнёр банковских программ. Помогаем школьникам (с 14 лет) и взрослым зарабатывать на оформлении карт и офферов.\n"
        "В августе партнёрам выплачено: <b>162 480 ₽</b> 💸\n\n"
        "Как это работает:\n"
        "• заполняешь короткую анкету,\n"
        "• получаешь персональную ссылку,\n"
        "• после подтверждения банком — забираешь выплату.\n\n"
        "Готов(-а) стартовать? Жми «Начать».",
        reply_markup=kb_welcome()
    )

@r.message(CommandStart())
async def start_plain(m: Message, state: FSMContext):
    await state.clear()
    await state.update_data(flow="plain", user_id=m.from_user.id)
    await m.answer(
        "Привет 👋 Это CardUP.\n\n"
        "Мы — официальный партнёр банковских программ. Помогаем школьникам (с 14 лет) и взрослым зарабатывать на оформлении карт и офферов.\n"
        "В августе партнёрам выплачено: <b>162 480 ₽</b> 💸\n\n"
        "Как это работает:\n"
        "• заполняешь короткую анкету,\n"
        "• получаешь персональную ссылку,\n"
        "• после подтверждения банком — забираешь выплату.\n\n"
        "Готов(-а) стартовать? Жми «Начать».",
        reply_markup=kb_welcome()
    )

# === Анкета ===
@r.callback_query(F.data == "start_form")
async def start_form(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Как тебя зовут? 🙂\n(нужно для обращения, например: Иван)")
    await state.set_state(Lead.name)
    await cb.answer()

@r.message(Lead.name)
async def get_name(m: Message, state: FSMContext):
    name = clean(m.text)
    if len(name) < 2:
        await m.answer("Имя слишком короткое. Введи настоящее имя 👇")
        return
    await state.update_data(name=name)
    await m.answer(f"Отлично, {name}! 🎉\nТеперь скажи, сколько тебе лет? (от 14+)")
    await state.set_state(Lead.age)

@r.message(Lead.age)
async def get_age(m: Message, state: FSMContext):
    s = clean(m.text)
    if not s.isdigit():
        await m.answer("Возраст числом. Сколько лет? (14–99)")
        return
    age = int(s)
    if age < 14 or age > 99:
        await m.answer("Подходит 14–99. Попробуй ещё раз 👇")
        return
    await state.update_data(age=age)
    suggested = f"@{m.from_user.username}" if getattr(m.from_user, "username", None) else "@username"
    await m.answer(
        "Последний шаг 🙌\n"
        "Оставь свой Telegram @username, чтобы менеджер смог связаться с тобой.\n"
        f"Например: <code>{suggested}</code>"
    )
    await state.set_state(Lead.tg)

@r.message(Lead.tg)
async def get_tg(m: Message, state: FSMContext):
    tg = clean(m.text)
    if not tg.startswith("@") or len(tg) < 3:
        await m.answer("Нужен ник с @ в начале. Пример: @yourname")
        return
    await state.update_data(tg=tg)
    data = await state.get_data()

    payload = {
        "user_id": data.get("user_id"),
        "flow": data.get("flow","plain"),
        "name": data.get("name"),
        "age": data.get("age"),
        "tg": tg
    }
    await notify_manager(payload)
    save_csv(payload)

    await m.answer(
        "Готово 🎉 Мы получили твою заявку!\n\n"
        "📣 Чтобы быть в теме и не пропускать офферы:\n"
        f"• Подпишись на наш <a href='{CHANNEL_LINK}'>основной канал</a> — там свежие задания и выплаты.\n"
        f"• Загляни в <a href='{REVIEWS_LINK}'>канал с отзывами</a> — реальные скрины и истории ребят.\n"
        f"• Сайт с условиями: <a href='{SITE_LINK}'>{SITE_LINK}</a>",
        reply_markup=kb_finish()
    )
    await state.clear()

# === Help ===
@r.message(Command("help"))
async def cmd_help(m: Message):
    await m.answer("Команды:\n/start — начать\n/help — помощь")

# === Запуск ===
async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        log.warning("delete_webhook: %s", e)
    try:
        if MANAGER_CHAT_ID:
            await bot.send_message(MANAGER_CHAT_ID, "✅ Бот запущен и слушает обновления.")
    except Exception as e:
        log.warning("send to admin failed: %s", e)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
