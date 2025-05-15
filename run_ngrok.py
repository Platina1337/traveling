import os
import subprocess
import time
import requests
import json

def run_ngrok():
    # Путь к ngrok.exe
    ngrok_path = os.path.join(os.getcwd(), 'ngrok.exe')
    
    # Проверяем, существует ли ngrok.exe
    if not os.path.exists(ngrok_path):
        print("ngrok.exe не найден в текущей директории!")
        return
    
    # Запускаем ngrok на порту 8000
    ngrok_process = subprocess.Popen([ngrok_path, 'http', '8000'])
    
    # Даем ngrok время на запуск
    time.sleep(2)
    
    try:
        # Получаем URL туннеля
        response = requests.get('http://localhost:4040/api/tunnels')
        tunnels = response.json()['tunnels']
        public_url = tunnels[0]['public_url']
        
        print("\n=== Ngrok запущен ===")
        print(f"Публичный URL: {public_url}")
        print("=====================\n")
        
        # Ждем, пока пользователь не нажмет Ctrl+C
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nОстанавливаем ngrok...")
        ngrok_process.terminate()
        print("Ngrok остановлен")

if __name__ == '__main__':
    run_ngrok() 