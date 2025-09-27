import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import re

# 🔐 Завантаження токена з .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не знайдено в змінних середовища")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# 📦 Словник для тимчасового зберігання результатів пошуку
track_results = {}


# -------------------------------- SOUND SEARCH -------------------------------- #

def create_main_menu():
    """Створює головне меню клавіатури"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    franko = types.KeyboardButton('Іван Якович')
    boi4uk = types.KeyboardButton('Бойчук')
    start = types.KeyboardButton("knopka")

    markup.row(boi4uk, franko)
    markup.row(start)
    return markup


@bot.message_handler(commands=["start"])
def main_menu(message):
    """Обробник команди /start"""
    markup = create_main_menu()
    bot.send_message(message.chat.id, "Вибери опцію:", reply_markup=markup)


# функції для кнопок
@bot.message_handler(func=lambda message: message.text in [
    "Іван Якович", "Бойчук", "хуй", "knopka", "darina"
])
def button2(message):
    """Обробник кнопок меню"""
    try:
        if message.text == "Іван Якович":
            if os.path.exists('123.png'):
                with open('123.png', 'rb') as photo:
                    bot.send_photo(message.chat.id, photo)
            else:
                bot.send_message(message.chat.id, "❌ Файл 123.png не знайдено")
        elif message.text == "darina":
            if os.path.exists('2025.png'):
                with open('2025.png', 'rb') as photo:
                    bot.send_photo(message.chat.id, photo)
            else:
                bot.send_message(message.chat.id, "❌ Файл 2222.png не знайдено")
        elif message.text == "Бойчук":
            bot.send_message(message.chat.id, "даун толстий")
        elif message.text == "хуй":
            bot.send_message(message.chat.id, "@krsqw")
        elif message.text == "knopka":
            bot.send_message(message.chat.id, "кнопка")
    except Exception as e:
        print(f"❌ Помилка в button2: {e}")
        bot.send_message(message.chat.id, "❌ Виникла помилка")


def search_soundcloud_tracks(query, limit=10):
    """Пошук треків на SoundCloud"""
    print(f"🔍 Пошук SoundCloud: {query}")
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'no_warnings': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"scsearch{limit}:{query}", download=False)
            if not search_results or 'entries' not in search_results:
                return []

            return [
                {'full_url': entry.get('url'), 'title': entry.get('title')}
                for entry in search_results.get('entries', [])
                if entry and entry.get('url')
            ]
    except Exception as e:
        print(f"❌ Помилка SoundCloud: {e}")
        return []


def search_youtube_tracks(query, limit=5):
    print(f"🔍 Пошук YouTube: {query}")
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'no_warnings': True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            if not search_results or 'entries' not in search_results:
                return []

            return [
                {'full_url': entry.get('url'), 'title': entry.get('title')}
                for entry in search_results.get('entries', [])
                if entry and entry.get('url')
            ]
    except Exception as e:
        print(f"❌ Помилка YouTube: {e}")
        return []


def download_mp3_from_url(url, platform="SoundCloud"):
    """Завантаження MP3 з URL"""
    print(f"⬇️ Завантаження ({platform}): {url}")

    # Створюємо папку downloads якщо не існує
    os.makedirs('downloads', exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Перевіряємо тривалість
            duration = info.get('duration', 0)
            if duration and duration > 5400:
                raise ValueError("⏳ Трек занадто довгий (макс 1.5 години)")

            # Завантажуємо файл
            info = ydl.extract_info(url, download=True)

            # Формуємо ім'я файлу
            original_filename = ydl.prepare_filename(info)
            base_name = os.path.splitext(original_filename)[0]
            filename = base_name + '.mp3'

            # Безпечне ім'я файлу
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

            # Якщо файл уже існує → додаємо суфікс
            if os.path.exists(safe_filename):
                base, ext = os.path.splitext(safe_filename)
                counter = 1
                new_name = f"{base}_{counter}{ext}"
                while os.path.exists(new_name):
                    counter += 1
                    new_name = f"{base}_{counter}{ext}"
                safe_filename = new_name

            # Перейменовуємо файл якщо потрібно
            if filename != safe_filename and os.path.exists(filename):
                os.rename(filename, safe_filename)
            elif os.path.exists(original_filename) and original_filename != safe_filename:
                os.rename(original_filename, safe_filename)

            return {
                'filename': safe_filename,
                'title': info.get('title', 'Unknown')
            }

    except Exception as e:
        print(f"❌ Помилка завантаження: {e}")
        raise


def download_mp3_from_soundcloud(url, fallback_query=None):
    """Завантаження з SoundCloud з fallback на YouTube"""
    try:
        return download_mp3_from_url(url, platform="SoundCloud")
    except Exception as e:
        print(f"❌ SoundCloud впав: {e}")
        if fallback_query:
            print("🔄 Пробуємо знайти на YouTube...")
            results = search_youtube_tracks(fallback_query, limit=1)
            if results:
                return download_mp3_from_url(results[0]['full_url'], platform="YouTube")
        raise e


# -------------------------------- HANDLERS -------------------------------- #

@bot.message_handler(commands=['music'])
def music_search_handler(message):
    """Обробник пошуку музики"""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "Вкажи назву треку або виконавця. Наприклад:\n/music Лук'ян Красавчік")
            return

        query = parts[1].strip()
        if not query:
            bot.send_message(message.chat.id, "Вкажи назву треку або виконавця.")
            return

        # Пошук на SoundCloud
        results = search_soundcloud_tracks(query)

        if not results:
            bot.send_message(message.chat.id, "На SoundCloud не знайдено, шукаємо на YouTube...")
            results = search_youtube_tracks(query)

            if not results:
                bot.send_message(message.chat.id, "дауннн 😢")
                return

        # Зберігаємо результати
        track_results[message.chat.id] = results

        # Створюємо клавіатуру
        markup = types.InlineKeyboardMarkup()
        for i, track in enumerate(results):
            title = (track.get('title') or "Без назви")[:35]
            markup.add(types.InlineKeyboardButton(
                text=f"{i + 1}. {title}",
                callback_data=f"download_{i}"
            ))

        bot.send_message(message.chat.id, "🎧 Вибери трек:", reply_markup=markup)

    except Exception as e:
        print(f"❌ Помилка в music_search_handler: {e}")
        bot.send_message(message.chat.id, "❌ Виникла помилка при пошуку")


@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def callback_download(call):
    """Обробник завантаження треку"""
    try:
        index = int(call.data.replace("download_", ""))
        chat_id = call.message.chat.id

        results = track_results.get(chat_id)
        if not results or index >= len(results):
            bot.send_message(chat_id, "❌ Трек не знайдено.")
            return

        track = results[index]
        url = track.get('full_url')
        query = track.get('title')

        if not url:
            bot.send_message(chat_id, "❌ URL треку не знайдено.")
            return

        bot.send_message(chat_id, "⏳ Завантаження треку...")

        result = download_mp3_from_soundcloud(url, fallback_query=query)

        if not os.path.exists(result['filename']):
            bot.send_message(chat_id, "❌ Файл не знайдено після завантаження.")
            return

        with open(result['filename'], 'rb') as audio:
            bot.send_audio(chat_id, audio, caption=f"✅ {result['title']}")

        # Видаляємо файл після відправки
        try:
            os.remove(result['filename'])
        except OSError as e:
            print(f"⚠️ Не вдалося видалити файл: {e}")

    except ValueError as ve:
        bot.send_message(call.message.chat.id, f"❌ {str(ve)}")
    except Exception as e:
        print(f"❌ Виникла помилка в callback_download: {e}")
        bot.send_message(call.message.chat.id, f"❌ Помилка: {str(e)}")
    finally:
        # Відповідаємо на callback щоб прибрати індикатор завантаження
        try:
            bot.answer_callback_query(call.id)
        except:
            pass


# -------------------------------- START BOT -------------------------------- #

if __name__ == "__main__":
    try:
        print("🤖 Запуск бота...")
        bot.remove_webhook()
        print("✅ Webhook видалено, запускаємо polling...")
        bot.polling(none_stop=True, interval=0, timeout=60)
    except KeyboardInterrupt:
        print("⏹️ Бот зупинено користувачем")
    except Exception as e:
        print("❌ Бот не запущено. Можливо, вже запущено інший інстанс.")
        print("Помилка:", e)