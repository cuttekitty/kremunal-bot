import os
import sys
import html
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import a2s
import telebot
from telebot import types

# Вставте сюди ваш актуальний токен бота
TOKEN = "8839101658:AAFaD3IVcrFDg3k86zsFgnInvC4R7uCJrak"
bot = telebot.TeleBot(TOKEN)

SERVER_IP = "91.211.118.131"
SERVER_PORT = 27015

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), PingHandler)
    server.serve_forever()

def get_server_status():
    address = (SERVER_IP, SERVER_PORT)
    try:
        info = a2s.info(address, timeout=5.0)
        try:
            players = a2s.players(address, timeout=5.0)
        except Exception:
            players = []

        text = (
            f"🎮 <b>{html.escape(info.server_name)}</b>\n\n"
            f"🟢 <b>Статус:</b> Онлайн\n"
            f"🗺 <b>Мапа:</b> <code>{html.escape(info.map_name)}</code>\n"
            f"👥 <b>Гравці:</b> {info.player_count}/{info.max_players}\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>\n\n"
        )

        active_players = [p for p in players if p.name and p.name.strip()]

        if active_players:
            text += "📋 <b>Список гравців онлайн:</b>\n"
            for idx, player in enumerate(active_players, start=1):
                clean_name = html.escape(player.name)
                text += f"{idx}. {clean_name} — <i>{player.score} фрагів</i>\n"
        else:
            if info.player_count > 0:
                text += "ℹ️ <i>Гравці на сервері, але нікнейми завантажуються...</i>"
            else:
                text += "😴 <i>На сервері зараз нікого немає.</i>"

        return text
    except Exception as err:
        return (
            "🔴 <b>Сервер не відповідає</b> або вимкнений.\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
        )

@bot.message_handler(commands=['start'])
def handle_start(message):
    remove_kb = types.ReplyKeyboardRemove()
    text = (
        f"Привіт, {message.from_user.first_name}!\n\n"
        "Бот моніторингу KREMUNAL працює за командами:\n"
        "👉 /status — дізнатися онлайн та переглянути список гравців\n"
        "👉 /info — інформація для підключення до сервера\n\n"
        "Також ви можете скористатися кнопкою <b>«Меню»</b> ліворуч унизу."
    )
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("🔄 Перевірити онлайн", callback_data="refresh_status"))
    bot.send_message(message.chat.id, text, reply_markup=remove_kb, parse_mode="HTML")
    bot.send_message(message.chat.id, "Швидкий запит:", reply_markup=inline_kb)

@bot.message_handler(commands=['status'])
def handle_status(message):
    status_text = get_server_status()
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("🔄 Оновити", callback_data="refresh_status"))
    bot.send_message(message.chat.id, status_text, reply_markup=inline_kb, parse_mode="HTML")

@bot.message_handler(commands=['info'])
def handle_info(message):
    text = (
        f"🎮 Сервер <b>KREMUNAL M9SO</b>\n"
        f"Підключення через консоль:\n<code>connect {SERVER_IP}:{SERVER_PORT}</code>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "refresh_status")
def handle_callback(call):
    bot.answer_callback_query(call.id)
    status_text = get_server_status()
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("🔄 Оновити", callback_data="refresh_status"))
    try:
        bot.edit_message_text(
            status_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=inline_kb,
            parse_mode="HTML"
        )
    except Exception:
        bot.send_message(call.message.chat.id, status_text, reply_markup=inline_kb, parse_mode="HTML")

if __name__ == "__main__":
    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()

    try:
        bot.set_my_commands([
            types.BotCommand("status", "Онлайн та список гравців"),
            types.BotCommand("info", "IP сервера та підключення"),
            types.BotCommand("start", "Головне меню")
        ])
    except Exception:
        pass

    bot.remove_webhook()
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
