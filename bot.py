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

# Фейковый веб-сервер для поддержания активности на Render
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

def fetch_server_data():
    """Получение данных через внешний веб-шлюз мониторинга"""
    endpoints = [
        f"https://api.steampowered.com/IGameServersService/GetServerList/v1/?filter=\\addr\\{SERVER_IP}:{SERVER_PORT}",
        f"https://api.gametracker.com/server/{SERVER_IP}:{SERVER_PORT}/",
    ]
    
    # Запрос к публичному API мониторинга игровых серверов
    url = f"https://api.battlemetrics.com/servers?filter[search]={SERVER_IP}&filter[game]=cs"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode())
            data = res.get('data', [])
            for s in data:
                attr = s.get('attributes', {})
                if str(attr.get('port')) == SERVER_PORT or SERVER_IP in attr.get('ip', ''):
                    return {
                        "name": attr.get('name', 'KREMUNAL CS 1.6'),
                        "map": attr.get('details', {}).get('map', 'Не определена'),
                        "players": attr.get('players', 0),
                        "max_players": attr.get('maxPlayers', 32),
                        "status": "Онлайн" if attr.get('status') == 'online' else "Оффлайн"
                    }
    except Exception as e:
        print(f"Battlemetrics error: {e}")

    # Запасной шлюз Valve Master / GS
    try:
        url_alt = f"https://api.cleanvoice.ru/ts3/cs/{SERVER_IP}:{SERVER_PORT}"
        req_alt = urllib.request.Request(url_alt, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_alt, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data and data.get('result'):
                return {
                    "name": data.get('name', 'KREMUNAL CS 1.6'),
                    "map": data.get('map', 'Не определена'),
                    "players": data.get('players', 0),
                    "max_players": data.get('maxplayers', 32),
                    "status": "Онлайн"
                }
    except Exception as e:
        print(f"Alt error: {e}")

    return None

def get_server_status():
    info = fetch_server_data()
    
    if info:
        text = (
            f"🎮 <b>{html.escape(str(info['name']))}</b>\n\n"
            f"🟢 <b>Статус:</b> {info['status']}\n"
            f"🗺 <b>Карта:</b> <code>{html.escape(str(info['map']))}</code>\n"
            f"👥 <b>Игроки:</b> {info['players']}/{info['max_players']}\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>\n"
        )
        return text

    return (
        "🔴 <b>Сервер не отвечает</b> или выключен.\n"
        f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    inline_kb = types.InlineKeyboardMarkup()
    btn_status = types.InlineKeyboardButton("🔄 Проверить статус", callback_data="status")
    inline_kb.add(btn_status)

    reply_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add("📊 Мониторинг", "ℹ️ Информация")

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\nБот мониторинга KREMUNAL готов к работе.",
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
        f"Подключение к серверу:\n<code>connect {SERVER_IP}:{SERVER_PORT}</code>",
        parse_mode="HTML"
    )

if __name__ == "__main__":
    threading.Thread(target=run_http_server, daemon=True).start()
    print("Бот успешно запущен!")
    bot.infinity_polling()
