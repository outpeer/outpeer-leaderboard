import gspread
import random
import telebot
import time
from telebot import types
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Define maximum number of retry attempts
MAX_RETRY_ATTEMPTS = 5

# Define maximum backoff time (in seconds)
MAX_BACKOFF_TIME = 64

# Telegram Bot Token
bot = telebot.TeleBot('6934266191:AAG8xqdZ_FE3U8Dm4p4HcegEZZEuhlX8eeo')

#dp = bot.dispatcher
gc = gspread.service_account(filename="creds.json")
sh = gc.open("Leader Board outpeer.kz courses")

def exponential_backoff(retry_attempt):
  delay = min(2 ** retry_attempt + random.random(), MAX_BACKOFF_TIME)
  time.sleep(delay)

user_data = {}
def handle_with_exponential_backoff(func):
  def wrapper(message):
      retry_attempt = 0
      while retry_attempt < MAX_RETRY_ATTEMPTS:
          try:
              return func(message)
          except Exception as e:
              print(f"Error occurred: {e}")
              retry_attempt += 1
              if retry_attempt < MAX_RETRY_ATTEMPTS:
                  exponential_backoff(retry_attempt)
              else:
                  # Log or handle the error after maximum retry attempts
                  print("Maximum retry attempts reached. Exiting...")
                  return
  return wrapper
# Start message
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ask_position = types.KeyboardButton(text='Узнать свое место в таблице лидеров')
    btn_ask_attendance = types.KeyboardButton(text='Узнать процент посещения занятий')
    btn_ask_hw = types.KeyboardButton(text='Узнать оценки за домашние задания')
    # btn_ask_capstone = types.KeyboardButton(text='Узнать оценку за Capstone Project')
    # btn_miss_form = types.KeyboardButton(text='Заполнить форму о пропуске занятий')

    markup.row(btn_ask_position)
    markup.row(btn_ask_attendance)
    markup.row(btn_ask_hw)
    # markup.row(btn_ask_capstone)
    # markup.row(btn_miss_form)

    bot.send_message(message.from_user.id, "Доброго времени суток, дорогой студент [outpeer.kz](https://programs.outpeer.kz)! Чем я могу вам помочь?", reply_markup=markup, parse_mode='Markdown')

# Check position
@bot.message_handler(func=lambda message: message.text == 'Узнать свое место в таблице лидеров')
def choose_course_position(message):
    user_id = message.from_user.id

    # Create ReplyKeyboardMarkup for course selection
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ds = types.KeyboardButton(text='Data Science')
    btn_da = types.KeyboardButton(text='Data Analytics')
    btn_pe = types.KeyboardButton(text='Python Engineering')
    btn_be = types.KeyboardButton(text='Blockchain Engineering')
    btn_csr = types.KeyboardButton(text='Computer Science & Robotics')
    btn_back = types.KeyboardButton(text='Вернуться в главное меню')

    markup.row(btn_ds)
    markup.row(btn_da)
    markup.row(btn_pe)
    markup.row(btn_be)
    markup.row(btn_csr)
    markup.row(btn_back)

    bot.send_message(user_id, "На каком курсе outpeer.kz вы обучаетесь?", reply_markup=markup)
    bot.register_next_step_handler(message, handle_course_selection)

def handle_course_selection(message):
    user_id = message.from_user.id
    course_mapping = {
        'Data Science': 'LeaderBoard TO DS2',
        'Data Analytics': 'LeaderBoard TO DA2',
        'Python Engineering': 'LeaderBoard TO PE2',
        'Blockchain Engineering': 'LeaderBoard TO BE2',
        'Computer Science & Robotics': 'LeaderBoard TO CS&R2'
    }

    if message.text in course_mapping:
        sheet_name = course_mapping[message.text]
        user_data[user_id] = {'sheet': sheet_name}
        try:
            sheet = sh.worksheet(sheet_name)
            # Ask for IIN number and remove the inline keyboard
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn_back = types.KeyboardButton(text='Вернуться в главное меню')
            markup.row(btn_back)
            bot.send_message(user_id, f"Введите пожалуйста свой ИИН:", reply_markup=markup)
            bot.register_next_step_handler(message, handle_iin_position)
        except gspread.WorksheetNotFound:
            bot.send_message(user_id, f"Sheet for {sheet_name} not found.")
    elif message.text == 'Вернуться в главное меню':
      button_back(message)

def button_back(message):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  btn_ask_position = types.KeyboardButton(text='Узнать свое место в таблице лидеров')
  btn_ask_attendance = types.KeyboardButton(text='Узнать процент посещения занятий')
  btn_ask_hw = types.KeyboardButton(text='Узнать оценки за домашние задания')
  # btn_ask_capstone = types.KeyboardButton(text='Узнать оценку за Capstone Project')
  # btn_miss_form = types.KeyboardButton(text='Заполнить форму о пропуске занятий')

  markup.row(btn_ask_position)
  markup.row(btn_ask_attendance)
  markup.row(btn_ask_hw)
  # markup.row(btn_ask_capstone)
  # markup.row(btn_miss_form)

  bot.send_message(message.from_user.id, "Чем я могу вам помочь?", reply_markup=markup, parse_mode='Markdown')

@handle_with_exponential_backoff
def handle_iin_position(message):
    user_id = message.from_user.id

    if user_id in user_data and 'sheet' in user_data[user_id]:
        if message.text == 'Вернуться в главное меню':
          del user_data[user_id]
          button_back(message)
          return
        user_data[user_id]['iin'] = message.text

        try:
            # Access the corresponding sheet in the Google Spreadsheet
            sheet_name = user_data[user_id]['sheet']
            sheet = sh.worksheet(sheet_name)

            # Find user by IIN in the sheet
            iin_column = sheet.col_values(3)
            user_row = None
            for i, iin_value in enumerate(iin_column):
                if iin_value == user_data[user_id]['iin']:
                    user_row = i + 1
                    break

            if user_row is not None:
                name = sheet.cell(user_row, 2).value
                if sheet_name == 'LeaderBoard TO CS&R2':
                  rating = sheet.cell(user_row, 10).value
                else:
                  rating = sheet.cell(user_row, 11).value
                total_students = sum(1 for value in sheet.col_values(1) if value) - 1

                bot.send_message(user_id, f"{name}, в таблице вы занимаете {rating} место из {total_students}.")
                button_back(message)
                return
            else:
                # If IIN is not correct, ask again
                bot.send_message(user_id, "ИИН введен некорректно. Пожалуйста, введите свой ИИН еще раз.")
                return

        except gspread.WorksheetNotFound:
            bot.send_message(user_id, f"Sheet for {sheet_name} not found.")

        del user_data[user_id]

# Check attendance
@bot.message_handler(func=lambda message: message.text == 'Узнать процент посещения занятий')
def choose_course_attendance(message):
    user_id = message.from_user.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ds = types.KeyboardButton(text='Data Science')
    btn_da = types.KeyboardButton(text='Data Analytics')
    btn_pe = types.KeyboardButton(text='Python Engineering')
    btn_be = types.KeyboardButton(text='Blockchain Engineering')
    btn_csr = types.KeyboardButton(text='Computer Science & Robotics')
    btn_back = types.KeyboardButton(text='Вернуться в главное меню')

    markup.row(btn_ds)
    markup.row(btn_da)
    markup.row(btn_pe)
    markup.row(btn_be)
    markup.row(btn_csr)
    markup.row(btn_back)

    bot.send_message(user_id, "На каком курсе outpeer.kz вы обучаетесь?", reply_markup=markup)
    bot.register_next_step_handler(message, button_click_attendance)

def button_click_attendance(message):
  user_id = message.from_user.id

  sheet_mapping = {
      'Data Science': """Attendance TO DS'2""",
      'Data Analytics': """Attendance TO DA'2""",
      'Python Engineering': """Attendance TO PE'2""",
      'Blockchain Engineering': """Attendance TO BE'2""",
      'Computer Science & Robotics': """Attendance TO CS&R'2"""
  }

  if message.text in sheet_mapping:
    sheet_name = sheet_mapping[message.text]
    user_data[user_id] = {'sheet': sheet_name}
    try:
        sheet = sh.worksheet(sheet_name)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_back = types.KeyboardButton(text='Вернуться в главное меню')
        markup.row(btn_back)
        bot.send_message(user_id, f"Введите пожалуйста свой ИИН:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_iin_attendance)
    except gspread.WorksheetNotFound:
        bot.send_message(user_id, f"Sheet for {sheet_name} not found.")
  elif message.text == 'Вернуться в главное меню':
    button_back(message)
    return

@handle_with_exponential_backoff
def handle_iin_attendance(message):
    user_id = message.from_user.id

    if user_id in user_data and 'sheet' in user_data[user_id]:
        # User has chosen a sheet, store IIN and proceed
        user_data[user_id]['iin'] = message.text
        if message.text == 'Вернуться в главное меню':
          del user_data[user_id]
          button_back(message)
          return
        try:
            sheet_name = user_data[user_id]['sheet']
            sheet = sh.worksheet(sheet_name)

            headers = sheet.row_values(1)
            attended_lessons_index = headers.index('Кол-во посещенный занятий') + 1
            passed_lessons_index = headers.index('Кол-во пройденных занятий') + 1
            all_lessons_index = headers.index('Общее количество занятий') + 1
            attendance_index = headers.index('Процент посещения за пройденные уроки') + 1

            iin_column = sheet.col_values(3)
            user_row = None
            for i, iin_value in enumerate(iin_column):
                if iin_value == user_data[user_id]['iin']:
                    user_row = i + 1
                    break

            if user_row is not None:
                name = sheet.cell(user_row, 2).value
                attended_lessons = sheet.cell(user_row, attended_lessons_index).value
                passed_lessons = sheet.cell(user_row, passed_lessons_index).value
                all_lessons = sheet.cell(user_row, all_lessons_index).value
                attendance = sheet.cell(user_row, attendance_index).value

                bot.send_message(user_id, f"{name}, прошло {passed_lessons} уроков из {all_lessons}. Вы посетили {attended_lessons} занятий. Ваш процент посещаемости уроков - {attendance}")
                button_back(message)
                return
            else:
              bot.send_message(user_id, "ИИН введен некорректно. Пожалуйста, введите свой ИИН еще раз.")
              return

        except gspread.WorksheetNotFound:
            bot.send_message(user_id, f"Sheet for {sheet_name} not found.")

        del user_data[user_id]

# Check homework
@bot.message_handler(func=lambda message: message.text == 'Узнать оценки за домашние задания')
def choose_course_homework(message):
    user_id = message.from_user.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_ds = types.KeyboardButton(text='Data Science')
    btn_da = types.KeyboardButton(text='Data Analytics')
    btn_pe = types.KeyboardButton(text='Python Engineering')
    btn_be = types.KeyboardButton(text='Blockchain Engineering')
    btn_csr = types.KeyboardButton(text='Computer Science & Robotics')
    btn_back = types.KeyboardButton(text='Вернуться в главное меню')

    markup.row(btn_ds)
    markup.row(btn_da)
    markup.row(btn_pe)
    markup.row(btn_be)
    markup.row(btn_csr)
    markup.row(btn_back)

    bot.send_message(user_id, "На каком курсе outpeer.kz вы обучаетесь?", reply_markup=markup)
    bot.register_next_step_handler(message, button_click_homework)

def button_click_homework(message):
  user_id = message.from_user.id

  sheet_mapping = {
      'Data Science': """HW TO DS'2""",
      'Data Analytics': """HW TO DA'2""",
      'Python Engineering': """HW TO PE'2""",
      'Blockchain Engineering': """HW TO BE'2""",
      'Computer Science & Robotics': """HW TO CS&R'2"""
  }

  if message.text in sheet_mapping:
    sheet_name = sheet_mapping[message.text]
    user_data[user_id] = {'sheet': sheet_name}
    try:
        sheet = sh.worksheet(sheet_name)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_back = types.KeyboardButton(text='Вернуться в главное меню')
        markup.row(btn_back)
        bot.send_message(user_id, f"Введите пожалуйста свой ИИН:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_iin_homework)
    except gspread.WorksheetNotFound:
        bot.send_message(user_id, f"Sheet for {sheet_name} not found.")
  elif message.text == 'Вернуться в главное меню':
    button_back(message)
    return
@handle_with_exponential_backoff
def handle_iin_homework(message):
    user_id = message.from_user.id

    if user_id in user_data and 'sheet' in user_data[user_id]:
        user_data[user_id]['iin'] = message.text
        if message.text == 'Вернуться в главное меню':
          del user_data[user_id]
          button_back(message)
          return
        try:
            sheet_name = user_data[user_id]['sheet']
            sheet = sh.worksheet(sheet_name)

            headers = sheet.row_values(1)
            total_hw_index = headers.index('Кол-во д/з') + 1
            passed_hw_index = headers.index('Total') + 1

            iin_column = sheet.col_values(3)
            user_row = None
            for i, iin_value in enumerate(iin_column):
                if iin_value == user_data[user_id]['iin']:
                    user_row = i + 1
                    break

            if user_row is not None:
                name = sheet.cell(user_row, 2).value
                total_hw = sheet.cell(user_row, total_hw_index).value
                passed_hw = sheet.cell(user_row, passed_hw_index).value

                bot.send_message(user_id, "Пожалуйста, подождите, идет подсчет...")

                hw_percentages = []
                for i in range(headers.index("Тип студента") + 2, total_hw_index, +1):
                  header_name = headers[i - 1]
                  hw = sheet.cell(user_row, i).value
                  if hw:
                      hw_percentages.append((header_name, hw))
                response = f"{name}, с начала курса было задано {total_hw} домашних заданий. Ваша средняя оценка по всем домашним работам -  {passed_hw}/100.\n"
                for header, value in hw_percentages:
                  response += f"{header} - {value}\n"

                bot.send_message(user_id, response)
                button_back(message)
                return
            else:
              bot.send_message(user_id, "ИИН введен некорректно. Пожалуйста, введите свой ИИН еще раз.")
              return

        except gspread.WorksheetNotFound:
            bot.send_message(user_id, f"Sheet for {sheet_name} not found.")

        del user_data[user_id]

bot.polling(none_stop=True, interval=0)