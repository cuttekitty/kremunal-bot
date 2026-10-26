import html
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import a2s
import telebot
from telebot import types

TOKEN = "8839101658:AAFaD3IVcrFDg3k86zsFgnInvC4R7uCJrak"
bot = telebot.TeleBot(TOKEN)

SERVER_IP = "91.211.118.131"
SERVER_PORT = 27015

# HTTP-сервер для поддержания статуса Live на Render
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
                text += "ℹ️ <i>Игроки на сервере, но ники загружаются...</i>"
            else:
                text += "😴 <i>На сервере сейчас никого нет.</i>"

        return text
    except Exception as err:
        print(f"Ошибка опроса сервера: {err}")
        return (
            "🔴 <b>Сервер не отвечает</b> или выключен.\n"
            f"🔌 <b>IP:</b> <code>connect {SERVER_IP}:{SERVER_PORT}</code>"
        )

# Команда /start
@bot.message_handler(commands=['start'])
def handle_start(message):
