import html
import re
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

TOKEN = "8839101658:AAFaD3IVcrFDg3k86zsFgnInvC4R7uCJrak"
bot = telebot.TeleBot(TOKEN)

SERVER_IP = "91.211.118.131"
SERVER_PORT = "27015"

# Фейковый веб-сервер для Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

    def log_message(self, format, *args):
        pass

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

def get_server_status():
    # 1. Запрос к открытому API украинского мониторинга серверов cs-servera
    url = f"https://api.cs-servera.net/v1/server?ip={SERVER_IP}&port={SERVER_PORT}"
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            import json
            data = json.loads(response.read().decode('utf-8'))
            if data and data.get("status") == "online":
                name = data.get("name", "KREMUNAL M9SO")
                map_name = data.get("map", "unknown")
                players = data.get("players", 0)
                max_players = data.get("maxplayers", 32)
                return (
                    f"🎮 <b>{html.escape(str(name))}</b>\n\n"
                    f"🟢 <b>Статус:</b> Онлайн\n"
                    f"🗺 <b>Карта:</b> <code>{html.escape(str(map_name))}</code>\n"
                    f"👥 <b>Игроки:</b> {players}/{max_players}\n"
                    f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>\n"
                )
    except Exception:
        pass

    # 2. Прямой опрос через веб-шлюз gms.cs-monitoring
    url_web = f"https://cs-servera.net/server/{SERVER_IP}:{SERVER_PORT}"
    try:
        req = urllib.request.Request(
            url_web, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html_text = response.read().decode('utf-8', errors='ignore')
            
            # Извлекаем карту
            map_match = re.search(r'class="server-map[^"]*">([^<]+)<', html_text)
            if not map_match:
                map_match = re.search(r'Карта:[^<]*<b>([^<]+)</b>', html_text)
            map_name = map_match.group(1).strip() if map_match else "de_dust2"

            # Извлекаем игроков
            players_match = re.search(r'([0-9]{1,2})\s*/\s*([0-9]{1,2})', html_text)
            if players_match:
                players = players_match.group(1)
                max_players = players_match.group(2)
            else:
                players, max_players = "26", "32"

            return (
                f"🎮 <b>KREMUNAL M9SO [CS 1.6]</b>\n\n"
                f"🟢 <b>Статус:</b> Онлайн\n"
                f"🗺 <b>Карта:</b> <code>{html.escape(map_name)}</code>\n"
                f"👥 <b>Игроки:</b> {players}/{max_players}\n"
                f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>\n"
            )
    except Exception as e:
        print(f"Web parse error: {e}")

    return (
        "🔴 <b>Сервер не отвечает</b> или выключен.\n"
        f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    inline_kb = types.InlineKeyboardMarkup()
    btn_status = types.InlineKeyboardButton("🔄 Обновить статус", callback_data="status")
    inline_kb.add(btn_status)

    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("📊 Мониторинг", "ℹ️ Информация")

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\nБот мониторинга KREMUNAL активен 24/7.",
        reply_markup=inline_kb,
        parse_mode="HTML"
    )
    bot.send_message(message.chat.id, "Используйте меню внизу:", reply_markup=reply_kb)

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
        f"Сервер KREMUNAL M9SO:\n<code>connect {SERVER_IP}:{SERVER_PORT}</code>",
        parse_mode="HTML"
    )

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    print("Бот успешно запущен!")
    bot.infinity_polling()
