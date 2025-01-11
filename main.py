import telebot
import os
import psutil
import pyautogui
import time
import cv2
import numpy as np

API_TOKEN = ""

bot = telebot.TeleBot(API_TOKEN)

ALLOWED_USERS = []
ACCESS_PASSWORD = "0"


def is_allowed_user(user_id):
    return user_id in ALLOWED_USERS


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if is_allowed_user(user_id):
        bot.reply_to(message, "Добро пожаловать! Напишите /help для списка команд.")
    else:
        bot.reply_to(message, "Для доступа введите пароль командой /password <ваш пароль>.")


@bot.message_handler(commands=['password'])
def check_password(message):
    try:
        user_id = message.from_user.id
        if is_allowed_user(user_id):
            bot.reply_to(message, "Вы уже авторизованы!")
            return

        password = message.text.split(' ', 1)[1]
        if password == ACCESS_PASSWORD:
            ALLOWED_USERS.append(user_id)
            bot.reply_to(message, "Пароль принят! Вы добавлены в список разрешённых пользователей.")
        else:
            bot.reply_to(message, "Неверный пароль. Доступ запрещён.")
    except IndexError:
        bot.reply_to(message, "Пожалуйста, укажите пароль в формате: /password <ваш пароль>.")


@bot.message_handler(commands=['help'])
def send_help(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "У вас нет доступа! Введите пароль командой /password <ваш пароль>.")
        return
    help_text = (
        "Команды:\n"
        "/help - Показать это сообщение\n"
        "/screenshot - Сделать скриншот рабочего стола\n"
        "/resources - Показать загрузку системы (CPU, RAM, диск)\n"
        "/processes - Показать список активных процессов\n"
        "/kill <PID> - Завершить процесс по его PID\n"
        "/record - Записать 10 секунд видео рабочего стола и отправить"
    )
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['screenshot'])
def screenshot(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "У вас нет доступа! Введите пароль командой /password <ваш пароль>.")
        return
    try:
        screenshot_path = "screenshot.png"
        pyautogui.screenshot(screenshot_path)
        with open(screenshot_path, 'rb') as screenshot_file:
            bot.send_photo(message.chat.id, screenshot_file)
        os.remove(screenshot_path)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")


@bot.message_handler(commands=['resources'])
def show_resources(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "У вас нет доступа! Введите пароль командой /password <ваш пароль>.")
        return
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        response = (
            f"Загрузка CPU: {cpu_usage}%\n"
            f"Использование RAM: {memory.percent}% ({memory.used // (1024 ** 2)} MB из {memory.total // (1024 ** 2)} MB)\n"
            f"Доступно на диске: {disk.free // (1024 ** 3)} GB из {disk.total // (1024 ** 3)} GB"
        )
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")


def record_screen(duration=10, output_file="recording.avi"):
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_file, fourcc, 20.0, screen_size)

    start_time = time.time()
    while time.time() - start_time < duration:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    out.release()


@bot.message_handler(commands=['record'])
def record_and_send(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "У вас нет доступа! Введите пароль командой /password <ваш пароль>.")
        return
    try:
        bot.reply_to(message, "Начинаю запись экрана на 10 секунд...")
        video_file = "recording.avi"
        record_screen(duration=10, output_file=video_file)
        with open(video_file, "rb") as video:
            bot.send_video(message.chat.id, video)
        os.remove(video_file)
    except Exception as e:
        bot.reply_to(message, f"Ошибка при записи: {str(e)}")


@bot.message_handler(commands=['processes'])
def list_processes(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "У вас нет доступа! Введите пароль командой /password <ваш пароль>.")
        return
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            processes.append(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, CPU: {proc.info['cpu_percent']}%")
        processes_text = "\n".join(processes[:50])  # Ограничиваем список первыми 50 процессами
        bot.reply_to(message, f"Активные процессы:\n{processes_text}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при получении списка процессов: {str(e)}")


@bot.message_handler(commands=['kill'])
def kill_process(message):
    if not is_allowed_user(message.from_user.id):
        bot.reply_to(message, "У вас нет доступа! Введите пароль командой /password <ваш пароль>.")
        return
    try:
        pid = int(message.text.split(' ', 1)[1])
        process = psutil.Process(pid)
        process.terminate()
        bot.reply_to(message, f"Процесс с PID {pid} завершён.")
    except IndexError:
        bot.reply_to(message, "Пожалуйста, укажите PID в формате: /kill <PID>")
    except psutil.NoSuchProcess:
        bot.reply_to(message, "Процесс с указанным PID не найден.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")


bot.polling()
