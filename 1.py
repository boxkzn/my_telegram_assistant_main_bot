import requests

# Токен вашего бота
bot_token = 'YOUR_BOT_TOKEN'

# URL для отправки запросов к API Telegram
base_url = f'https://api.telegram.org/bot7442243457:AAEkTqRkNjKTtUgps-CDxlQJlgCg9dXgioE'

# Метод для получения обновлений
response = requests.get(f'{base_url}/getUpdates')

# Проверка успешности запроса
if response.status_code == 200:
    updates = response.json()
    for update in updates['result']:
        # Проверка наличия сообщения
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            chat_type = update['message']['chat']['type']
            if chat_type == 'group' or chat_type == 'supergroup':
                print(f'Group ID: {chat_id}')
else:
    print(f'Error {response.status_code}: {response.text}')
