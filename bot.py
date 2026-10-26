import html
import json
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

TOKEN = "8839101658:AAG5Lot8Lk0YsemHgWLDCRaUWzZSdPtQsSs"
bot = telebot.TeleBot(TOKEN)

SERVER_IP = "91.211.118.131"
SERVER_PORT = "27015"

# Фейковый веб-сервер для поддержания статуса Live на Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

    def log_message(self, format, *args):
        pass

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

def get_server_status():
    # Запрос через открытый API игрового мониторинга Top-MS / GS
    url = f"https://api.top-ms.ru/server/{SERVER_IP}:{SERVER_PORT}"
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            if data and data.get("status") == 1:
                name = data.get("name", "KREMUNAL CS 1.6")
                map_name = data.get("map", "Не указана")
                players = data.get("players", 0)
                max_players = data.get("maxplayers", 32)
                
                text = (
                    f"🎮 <b>{html.escape(name)}</b>\n\n"
                    f"🟢 <b>Статус:</b> Онлайн\n"
                    f"🗺 <b>Карта:</b> <code>{html.escape(map_name)}</code>\n"
                    f"👥 <b>Игроки:</b> {players}/{max_players}\n"
                    f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>\n"
                )
                return text
    except Exception as e:
        print(f"Top-MS API error: {e}")

    # Запасной опрос через Valve GameServer Directory API
    try:
        url_alt = f"https://api.steampowered.com/IGameServersService/GetServerList/v1/?filter=\\addr\\{SERVER_IP}:{SERVER_PORT}"
        req_alt = urllib.request.Request(url_alt, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_alt, timeout=5) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            servers = result.get("response", {}).get("servers", [])
            if servers:
                srv = servers[0]
                text = (
                    f"🎮 <b>{html.escape(srv.get('name', 'KREMUNAL CS 1.6'))}</b>\n\n"
                    f"🟢 <b>Статус:</b> Онлайн\n"
                    f"🗺 <b>Карта:</b> <code>{html.escape(srv.get('map', 'Не указана'))}</code>\n"
                    f"👥 <b>Игроки:</b> {srv.get('players', 0)}/{srv.get('max_players', 32)}\n"
                    f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>\n"
                )
                return text
    except Exception as e:
        print(f"Steam API error: {e}")

    return (
        "🔴 <b>Сервер не отвечает</b> или выключен.\n"
        f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    inline_kb = types.InlineKeyboardMarkup()
    btn_status = types.InlineKeyboardButton("🔄 Обновить онлайн", callback_data="status")
    inline_kb.add(btn_status)

    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("📊 Мониторинг", "ℹ️ Информация")

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\nБот мониторинга KREMUNAL запущен 24/7.",
        reply_markup=inline_kb,
        parse_mode="HTML"
    )
    bot.send_message(message.chat.id, "Используйте кнопки меню:", reply_markup=reply_kb)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id)
    if call.data == "status":
        text = get_server_status()
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Обновить", callback_data="status"))
        bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "📊 Мониторинг")
def btn_monitoring(message):
    text = get_server_status()
    bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def btn_info(message):
    bot.send_message(
        message.chat.id,
        f"Подключение к серверу:\n<code>connect {SERVER_IP}:{SERVER_PORT}</code>",
        parse_mode="HTML"
    )

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    print("Бот успешно запущен!")
    bot.infinity_polling()
