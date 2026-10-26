import html
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
import a2s

TOKEN = "8839101658:AAG5Lot8Lk0YsemHgWLDCRaUWzZSdPtQsSs"
bot = telebot.TeleBot(TOKEN)

SERVER_IP = "91.211.118.131"
SERVER_PORT = 27015

# Фейковый веб-сервер, чтобы Render не ругался на отсутствие порта
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

   def get_server_status():
    address = (SERVER_IP, SERVER_PORT)
    try:
        # Увеличиваем таймаут до 7 секунд
        info = a2s.info(address, timeout=7.0)
        try:
            players = a2s.players(address, timeout=7.0)
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
            for i, p in enumerate(active_players, start=1):
                clean_name = html.escape(p.name)
                text += f"{i}. {clean_name} — <i>{p.score} фрагов</i>\n"
        else:
            if info.player_count > 0:
                text += "ℹ️ <i>Игроки на сервере, но ники скрыты или загружаются...</i>"
            else:
                text += "😴 <i>На сервере сейчас никого нет.</i>"

        return text
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return (
            "🔴 <b>Сервер не отвечает</b> или выключен.\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
        )
        if active_players:
            text += "📋 <b>Список игроков онлайн:</b>\n"
            for i, p in enumerate(active_players, start=1):
                clean_name = html.escape(p.name)
                text += f"{i}. {clean_name} — <i>{p.score} фрагов</i>\n"
        else:
            if info.player_count > 0:
                text += "ℹ️ <i>Игроки подключаются или сервер скрывает ники...</i>"
            else:
                text += "😴 <i>На сервере сейчас никого нет.</i>"

        return text
    except Exception:
        return (
            "🔴 <b>Сервер не отвечает</b> или выключен.\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
        )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    inline_kb = types.InlineKeyboardMarkup()
    btn_status = types.InlineKeyboardButton("🔄 Проверить статус и игроков", callback_data="status")
    btn_rules = types.InlineKeyboardButton("📜 Правила", callback_data="rules")
    inline_kb.add(btn_status)
    inline_kb.add(btn_rules)

    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("📊 Мониторинг", "ℹ️ Информация")

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\nДобро пожаловать в мониторинг сервера KREMUNAL.",
        reply_markup=inline_kb,
        parse_mode="HTML"
    )
    bot.send_message(message.chat.id, "Также можете использовать кнопки внизу:", reply_markup=reply_kb)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)

    if call.data == "status":
        text = get_server_status()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="status"))
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

    elif call.data == "rules":
        rules_text = (
            "📜 <b>Правила сервера KREMUNAL:</b>\n"
            "1. Запрещено использование читов и сторонних скриптов.\n"
            "2. Запрещены оскорбления и токсичность.\n"
            "3. Уважайте игроков и администрацию."
        )
        bot.send_message(call.message.chat.id, rules_text, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "📊 Мониторинг")
def btn_monitoring(message):
    text = get_server_status()
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def btn_info(message):
    bot.send_message(
        message.chat.id,
        f"Сервер KREMUNAL\nПодключение: <code>connect {SERVER_IP}:{SERVER_PORT}</code>",
        parse_mode="HTML"
    )

if __name__ == "__main__":
    # Запускаем веб-сервер в фоновом потоке для Render
    threading.Thread(target=run_http_server, daemon=True).start()
    print("Бот успешно запущен и опрашивает список игроков!")
    bot.infinity_polling()
