import html
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import a2s
import telebot
from telebot import types

# Вставьте сюда актуальный токен вашего бота
TOKEN = "8839101658:AAG5Lot8Lk0YsemHgWLDCRaUWzZSdPtQsSs"
bot = telebot.TeleBot(TOKEN)

SERVER_IP = "91.211.118.131"
SERVER_PORT = 27015

# Локальный HTTP-сервер, чтобы Render держал сервис активным (Live)
class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass

def start_ping_server():
    server = HTTPServer(('0.0.0.0', 10000), PingHandler)
    server.serve_forever()

def get_server_status():
    address = (SERVER_IP, SERVER_PORT)
    try:
        # Увеличенное время ожидания ответа от сервера до 6 секунд
        info = a2s.info(address, timeout=6.0)
        
        try:
            players = a2s.players(address, timeout=6.0)
        except Exception:
            players = []

        text = (
            f"🎮 <b>{html.escape(info.server_name)}</b>\n\n"
            f"🟢 <b>Статус:</b> Онлайн\n"
            f"🗺 <b>Карта:</b> <code>{html.escape(info.map_name)}</code>\n"
            f"👥 <b>Игроки:</b> {info.player_count}/{info.max_players}\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>\n\n"
        )

        active_players = [p for p in players if p.name and p.name.strip()]

        if active_players:
            text += "📋 <b>Список игроков онлайн:</b>\n"
            for idx, player in enumerate(active_players, start=1):
                clean_name = html.escape(player.name)
                text += f"{idx}. {clean_name} — <i>{player.score} фрагов</i>\n"
        else:
            if info.player_count > 0:
                text += "ℹ️ <i>Игроки на сервере, но ники сейчас загружаются...</i>"
            else:
                text += "😴 <i>На сервере сейчас никого нет.</i>"

        return text
    except Exception as err:
        print(f"Ошибка опроса сервера CS: {err}")
        return (
            "🔴 <b>Сервер не отвечает</b> или выключен.\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
        )

# Меню и кнопки Telegram
@bot.message_handler(commands=['start'])
def handle_start(message):
    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("📊 Мониторинг", "ℹ️ Информация")

    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton("🔄 Проверить онлайн", callback_data="check_status"))

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\nМониторинг сервера KREMUNAL запущен.",
        reply_markup=inline_kb,
        parse_mode="HTML"
    )
    bot.send_message(message.chat.id, "Используйте кнопку внизу:", reply_markup=reply_kb)

@bot.callback_query_handler(func=lambda call: call.data == "check_status")
def handle_callback(call):
    bot.answer_callback_query(call.id)
    status_text = get_server_status()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="check_status"))
    bot.send_message(call.message.chat.id, status_text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "📊 Мониторинг" or msg.text == "Мониторинг")
def handle_monitoring_btn(message):
    status_text = get_server_status()
    bot.send_message(message.chat.id, status_text, parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.text == "ℹ️ Информация" or msg.text == "Информация")
def handle_info_btn(message):
    bot.send_message(
        message.chat.id,
        f"Сервер KREMUNAL M9SO\nПодключение в консоли: <code>connect {SERVER_IP}:{SERVER_PORT}</code>",
        parse_mode="HTML"
    )

if __name__ == "__main__":
    # Запуск фонового веб-сервера порта
    threading.Thread(target=start_ping_server, daemon=True).start()
    print("Бот успешно запущен!")
    
    # Защита от конфликта polling
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
