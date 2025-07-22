import os

import telebot
from telebot import types
from yt_dlp import YoutubeDL

Bot = telebot.TeleBot("7949282737:AAE6nVeoNoL-nMdF_U0h3itKKV1FClIoRBU")

# 🔧 Словник для збереження результатів пошуку по chat_id
track_results = {}

# команда /start
# @Bot.message_handler(commands=["start"])
# def button(information):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#
#     franko = types.KeyboardButton('Іван Якович')
#     boi4uk = types.KeyboardButton('Бойчук')
#     start = types.KeyboardButton("knopka")
#
#     markup.row(boi4uk, franko)
#     markup.row(start)
#     Bot.send_message(information.chat.id, "Привіт! Обери кнопку 👇", reply_markup=markup)
#
# # функції для кнопок
# @Bot.message_handler(func=lambda message: message.text in [
#     "Іван Якович", "Бойчук"
# ])
# def button2(message):
#     if message.text == "Іван Якович":
#         with open('123.png', 'rb') as photo:
#             Bot.send_photo(message.chat.id, photo)
#     elif message.text == "Бойчук":
#         Bot.send_message(message.chat.id, "даун толстий")


#--------------------------------------------------------------------------------------------------------------

# MUZIKA
def search_soundcloud_tracks(query, limit=10):
    print(f"🔍 Шукаємо (yt_dlp): {query}")
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"scsearch{limit}:{query}", download=False)
            if 'entries' not in search_results:
                return []

            results = []
            for entry in search_results['entries']:
                results.append({
                    'full_url': entry.get('url'),
                    'title': entry.get('title'),
                })
            return results
        except Exception as e:
            print(f"❌ Помилка під час пошуку: {e}")
            return []

def search_youtube_tracks(query, limit=5):
    print(f"🔍 Шукаємо на YouTube: {query}")
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            if 'entries' not in search_results:
                return []

            results = []
            for entry in search_results['entries']:
                results.append({
                    'full_url': entry.get('url'),
                    'title': entry.get('title'),
                })
            return results
        except Exception as e:
            print(f"❌ Помилка пошуку YouTube: {e}")
            return []

def download_mp3_from_soundcloud(url):
    print(f"⬇️ Завантаження: {url}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
        return {'filename': filename, 'title': info.get('title', 'Unknown')}

@Bot.message_handler(commands=['music'])
def music_search_handler(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        Bot.send_message(message.chat.id, "Вкажи назву треку або автора. Наприклад:\n/music Лук'ян Красавчік")
        return

    query = parts[1]
    results = search_soundcloud_tracks(query)

    if not results:
        Bot.send_message(message.chat.id, "на саунклауді не знайшло, шукаємр в ЮТЮБ:")
        results = search_youtube_tracks(query)

        if not results:
            Bot.send_message(message.chat.id, "помилка запиту, або треку не існує, або ви просто дібіл")
            return

    # Зберігаємо результати пошуку
    track_results[message.chat.id] = results

    markup = types.InlineKeyboardMarkup()
    for i, track in enumerate(results):
        title = track['title'][:35] or "Без назви"
        markup.add(
            types.InlineKeyboardButton(
                text=f"{i + 1}. {title}",
                callback_data=f"download_{i}"
            )
        )

    Bot.send_message(message.chat.id, "🎧 Вибери трек для завантаження:", reply_markup=markup)

@Bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def callback_download(call):
    index = int(call.data.replace("download_", ""))
    chat_id = call.message.chat.id

    results = track_results.get(chat_id)
    if not results or index >= len(results):
        Bot.send_message(chat_id, "❌ Трек не знайдено або список застарів. Спробуй ще раз.")
        return

    url = results[index]['full_url']
    try:
        Bot.send_message(chat_id, "⏳ Завантаження треку...")
        result = download_mp3_from_soundcloud(url)
        with open(result['filename'], 'rb') as audio:
            Bot.send_audio(chat_id, audio, caption=f"✅ {result['title']}")
        os.remove(result['filename'])
    except Exception as e:
        Bot.send_message(chat_id, f"❌ Помилка: {str(e)}")

Bot.polling(non_stop=True)
