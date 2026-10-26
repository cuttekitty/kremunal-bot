import html
import socket
import struct
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
import urllib.request
import json

TOKEN = "8839101658:AAG5Lot8Lk0YsemHgWLDCRaUWzZSdPtQsSs"
bot = telebot.TeleBot(TOKEN)

SERVER_IP = "91.211.118.131"
SERVER_PORT = 27015

# Фейковый веб-сервер для удержания порта на Render
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

    def log_message(self, format, *args):
        pass  # глушим лишние логи

def run_http_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

def query_goldsource_direct():
    """Прямой низкоуровневый опрос CS 1.6 по UDP сокету"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(4.0)
    try:
        # Запрос информации о сервере (A2S_INFO)
        req = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
        sock.sendto(req, (SERVER_IP, SERVER_PORT))
        data, _ = sock.recvfrom(4096)
        
        # Если сервер требует челлендж
        if len(data) >= 5 and data[4] == 0x41: # 'A'
            challenge = data[5:9]
            req = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00' + challenge
            sock.sendto(req, (SERVER_IP, SERVER_PORT))
            data, _ = sock.recvfrom(4096)

        if len(data) > 5 and (data[4] == 0x49 or data[4] == 0x6D): # 'I' или 'm'
            payload = data[5:]
            parts = payload.split(b'\x00')
