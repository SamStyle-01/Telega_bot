import sqlite3
import telebot
from telebot import types
import bcrypt
import joblib
import re

salt = joblib.load("salt")

bot = telebot.TeleBot("6578193845:AAFdBaFu7ZaioHvQb8wWgzMsZPOdluh2lUg")
conn = sqlite3.connect("C:\\Users\\Sam\\PycharmProjects\\SamProject\\datastud.db",
                       check_same_thread=False)
cursor = conn.cursor()

commands = ["📎 Добавить ссылку на работу", "📖 Посмотреть список доступных факультативов и наставников",
            "📌 Отобразить вакансии карьерного центра", "📋 Выбрать направление факультатива",
            "📸 Подтвердить оценку работы", "✉️ Отобразить портфолио", "🚪 Вернуться в главное меню",
            "📇 Отфильтровать список студентов по баллам"]

temp_name = ""              # Временное хранилище имени для подтверждения работ.
temp_num = ""               # Временное хранилище оценки для подтверждения работ.
career_center = False       # Пока находимся в карьерном центре.
choosing_elective = False   # Пока выбираем факультатив.
finding_student = False     # Пока ищем портфолио студента.

is_mark0 = False        # Оценивает ли преподаватель работу студента.
is_mark = False         # Оценивает ли преподаватель работу студента.
is_mark2 = False        # Оценивает ли преподаватель работу студента.
adding_link = False     # Добавляем ссылку.
averaging = False       # Фильтруем студентов по среднему баллу.

users_id = dict()   # Пользователи-студенты.
admin_user_id = []  # Пользователи-профессора.
all_users_id = set()  # Все пользователи.
employers_id = []   # Пользователи-профессора.

# Переменная содержит вообще все типы документов. Пока что добавление здесь новых типов документов не предусмотрено.
# Нужно для определения, кто какой доступ имеет.


def confirm_it(message):
    cursor.execute('SELECT * FROM Students WHERE Name = ?;', (temp_name,))
    data = cursor.fetchone()[3].split(" ")
    data[(int(temp_num) - 1) * 2] = str(message.text)
    conn.execute("UPDATE Students SET Links = ? WHERE Name = ?",
                 (' '.join(data), temp_name))
    conn.commit()


def is_valid_link(link):
    # Паттерн для проверки правильного написания ссылки
    link_pattern = r'^https?://(?:www\.)?\S+$'
    return re.match(link_pattern, link)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     text="Пройдите аутентификацию. Введите пароль...")
    all_users_id.add(message.from_user.id)
    bot.register_next_step_handler(message, authentication)


@bot.message_handler(content_types=['text'])
def authentication(message):
    # Если пользователь есть в базе разрешенных пользователей, то переходим к процедуре общения с ним.
    if message.from_user.id in users_id.keys() or message.from_user.id in admin_user_id or message.from_user.id in \
                                                                                           employers_id:
        bot.register_next_step_handler(message, func)
        func(message)

    else:  # Если нет, то требуем пароль.
        cursor.execute('SELECT * FROM Students WHERE Password = ?;',
                       (bcrypt.hashpw(message.text.encode(), salt),))
        code1 = cursor.fetchone()
        cursor.execute('SELECT * FROM Professors WHERE Password = ?;',
                       (bcrypt.hashpw(message.text.encode(), salt),))
        code2 = cursor.fetchone()
        cursor.execute('SELECT * FROM Employers WHERE Password = ?;',
                       (bcrypt.hashpw(message.text.encode(), salt),))
        code3 = cursor.fetchone()
        if code1 is not None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("📎 Добавить ссылку на работу")
            btn2 = types.KeyboardButton("📖 Посмотреть список доступных факультативов и наставников")
            btn3 = types.KeyboardButton("📌 Отобразить вакансии карьерного центра")
            btn4 = types.KeyboardButton("📋 Выбрать направление факультатива")
            markup.add(btn1, btn2, btn3, btn4)
            bot.send_message(message.chat.id, text='Аутентификация пройдена. Вы зашли в аккаунт пользователя ' +
                                                   code1[2] + ".\n" +
                                                   'Выберите один из предложенных вариантов:', reply_markup=markup)
            users_id[message.from_user.id] = code1[0]
            bot.register_next_step_handler(message, func)
        elif code2 is not None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("📸 Подтвердить оценку работы")
            btn2 = types.KeyboardButton("✉️ Отобразить портфолио")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, text='Вы вошли в систему как преподаватель ' +
                                                   code2[2] + ".\n" +
                                                   'Выберите один из предложенных вариантов:', reply_markup=markup)
            admin_user_id.append(message.from_user.id)
            bot.register_next_step_handler(message, func)
        elif code3 is not None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("✉️ Отобразить портфолио")
            btn2 = types.KeyboardButton("📇 Отфильтровать список студентов по баллам")
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, text='Вы вошли в систему как работодатель ' +
                                                   code3[2] + ".\n" +
                                                   'Выберите один из предложенных вариантов:', reply_markup=markup)
            employers_id.append(message.from_user.id)
            bot.register_next_step_handler(message, func)
        else:
            if message.from_user.id in all_users_id and message.text not in commands:
                bot.reply_to(message, 'Пароль неверный. Вы не прошли верификацию. Повторите попытку...')
            elif message.text in commands and message.from_user.id in all_users_id:
                bot.reply_to(message, 'У вас нет прав доступа для использования этой команды. Введите пароль...')
            else:
                bot.reply_to(message, 'Начните беседу с ботом, использовав команду /start.')


@bot.message_handler(content_types=['text'])
def func(message):
    global is_mark, is_mark2, adding_link, averaging, \
                temp_name, career_center, choosing_elective, finding_student, is_mark0, temp_num, employers_id
    if message.from_user.id in admin_user_id:
        if message.text == "📸 Подтвердить оценку работы":
            bot.send_message(message.chat.id, text="Укажите ФИО студента:")
            is_mark = True
        elif message.text == "✉️ Отобразить портфолио":
            bot.send_message(message.chat.id, text="Укажите ФИО студента:")
            finding_student = True
        elif message.text == "Прости. Прощай.":
            admin_user_id.remove(message.from_user.id)
            bot.send_message(message.chat.id, text="Введите пароль:")
        # Блок чистоты.
        elif is_mark:
            is_mark = False
            is_mark0 = True
            temp_name = message.text
            cursor.execute('SELECT * FROM Students WHERE Name = ?;', (message.text,))
            data = cursor.fetchone()
            data2 = data[3].split(" ")
            if len(data2) == 1 and data2[0] == '':
                bot.send_message(message.chat.id, "Студентом не было предоставлено никаких работ.")
                is_mark0 = False
            else:
                to_show = ""
                for el in range(len(data2)):
                    if el % 2:
                        to_show += str((el - 1) // 2 + 1) + ": " + str(data2[el]) + "\n"
                bot.send_message(message.chat.id, "Выберите номер работы, которую хотите оценить:" + "\n" + to_show)
        elif is_mark0:
            temp_num = message.text

            is_mark0 = False
            is_mark2 = True
            bot.send_message(message.chat.id, text="Укажите оценку за работу:")
        elif is_mark2:
            is_mark2 = False
            confirm_it(message)
            bot.send_message(message.chat.id, "Операция была завершена успешно!")
            temp_name = ""
            temp_num = ""

        elif finding_student:
            finding_student = False
            cursor.execute('SELECT * FROM Students WHERE Name = ?;', (message.text,))
            data = cursor.fetchone()
            if data is None:
                bot.send_message(message.chat.id, "Такого студента нет!")
            else:
                for_show = "Студент " + data[2] + ":\n\nСсылки на предыдущие работы студента:\n"
                if not len(data[3]):
                    for_show += "Отсутствуют.\n"
                else:
                    data2 = data[3].split(" ")
                    for i in range(len(data2)):
                        if i % 2:
                            if int(data2[i - 1]):
                                for_show += str((i - 1) // 2 + 1) + ". " + data2[i] + " оценка: " + data2[i - 1] + "\n"
                            else:
                                for_show += str((i - 1) // 2 + 1) + ". " + data2[i] + "\n"
                for_show += "\n"
                for_show += "Soft Skills: " + str(data[4]) + "\n"
                for_show += "Backend программирование: " + str(data[5]) + "\n"
                for_show += "Frontend Программирование: " + str(data[6]) + "\n"
                for_show += "Инженерные навыки: " + str(data[7]) + "\n"
                for_show += "Конструирование: " + str(data[8]) + "\n"
                for_show += "Дизайн: " + str(data[9]) + "\n"
                for_show += "Математика: " + str(data[10]) + "\n\n"
                average_mark = (data[4] + data[5] + data[6] + data[7] + data[8] + data[9] + data[10]) / 7
                for_show += "Средний балл по учебной программе: " + str(round(average_mark, 2)) + ".\n"
                for_show += "Достижения на факультативах: "
                if data[11] is not None:
                    for_show += data[11] + "."
                else:
                    for_show += "Отсутствуют."
                bot.send_message(message.chat.id, text=for_show)
        else:
            bot.send_message(message.chat.id, text="Ошибка. Такой команды нет.")
    elif message.from_user.id in users_id.keys() and not is_mark:
        if message.text == "📎 Добавить ссылку на работу":
            adding_link = True
            bot.send_message(message.chat.id, "Укажите ссылку:")
        elif message.text == "📖 Посмотреть список доступных факультативов и наставников":
            cursor.execute('SELECT * FROM Electives;')
            bot.send_message(message.chat.id, "Список доступных факультативов и возможных наставников:")
            for el in cursor.fetchall():
                for_show = el[1] + ".\n\n"
                el = el[2].split("; ")
                el = [elx.split(": ") for elx in el]
                for i in range(len(el)):
                    el[i][1] = el[i][1].split(", ")
                    el[i][0] = el[i][0].split(" / ")
                for i in range(len(el)):
                    for_show += (el[i][0][0] + ": " + str(el[i][0][1]) + " свободных мест.\n\nНавыки:\n🔸"
                                                    + "\n🔸".join(el[i][1]) + ".\n\n")
                bot.send_message(message.chat.id, for_show)
        elif message.text == "📌 Отобразить вакансии карьерного центра":
            career_center = True
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("🚪 Вернуться в главное меню")
            markup.add(btn1)
            cursor.execute('SELECT Indexes, Name FROM CareerCenters;')
            data = cursor.fetchall()
            data = sorted(data, key=lambda x: x[0])
            for_show = "Укажите номер интересующего карьерного центра.\n\n"
            for i in range(len(data)):
                for_show += str(data[i][0]) + ". " + data[i][1] + ".\n"

            bot.send_message(message.chat.id, text=for_show, reply_markup=markup)

        elif message.text == "🚪 Вернуться в главное меню":
            career_center = False
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("📎 Добавить ссылку на работу")
            btn2 = types.KeyboardButton("📖 Посмотреть список доступных факультативов и наставников")
            btn3 = types.KeyboardButton("📌 Отобразить вакансии карьерного центра")
            btn4 = types.KeyboardButton("📋 Выбрать направление факультатива")
            markup.add(btn1, btn2, btn3, btn4)
            bot.send_message(message.chat.id, text="Вы вернулись в главное меню.", reply_markup=markup)
        elif message.text == "📋 Выбрать направление факультатива":
            cursor.execute('SELECT DISTINCT Direction FROM Electives')
            data = cursor.fetchall()
            for_show = "Укажите номер требуемого направления:\n"
            if len(data):
                for i in range(len(data)):
                    for_show += "🔻 " + data[i][0] + ".\n"
                bot.send_message(message.chat.id, text=for_show)
                choosing_elective = True
            else:
                bot.send_message(message.chat.id, text="Такого направления ещё нет.")
        elif message.text == "Прости. Прощай.":
            del users_id[message.from_user.id]
            bot.send_message(message.chat.id, text="Введите пароль:")
        # Блок чистоты.
        elif choosing_elective:
            choosing_elective = False
            cursor.execute('SELECT Name FROM Electives WHERE Direction = ?', (message.text,))
            data = cursor.fetchall()
            for i in range(len(data)):
                data[i] = data[i][0]
            bot.send_message(message.chat.id, text="Выборка факультативов по направлению:\n✔️" + "\n✔️".join(data))
        elif career_center:
            cursor.execute('SELECT * FROM Students WHERE Indexes = ?;',
                           (users_id[message.from_user.id],))
            student = cursor.fetchone()
            cursor.execute('SELECT * FROM CareerCenters WHERE Indexes = ?;',
                           (message.text,))
            requirements = cursor.fetchone()
            result = []
            for i in range(7):
                result.append(int(student[i + 4] - int(requirements[i + 2])))
            has_negatives = any(x < 0 for x in result)
            if not has_negatives:
                bot.send_message(message.chat.id, "Ваши навыки достаточны, чтобы пройти на вакансию этого "
                                                  "карьерного центра.")
            else:
                for_show = "Вам не хватает следующих навыков:\n\n"
                if result[0] < 0:
                    for_show += "Soft Skills: " + str(-result[0]) + " единиц.\n"
                if result[1] < 0:
                    for_show += ("Backend Программирование: " + str(-result[1]) + " единиц.\n")
                if result[2] < 0:
                    for_show += ("Frontend Программирование: " + str(-result[2]) + " единиц.\n")
                if result[3] < 0:
                    for_show += ("Навык инженерии: " + str(-result[3]) + " единиц.\n")
                if result[4] < 0:
                    for_show += ("Навык конструирования: " + str(-result[4]) + " единиц.\n")
                if result[5] < 0:
                    for_show += ("Навык дизайна: " + str(-result[5]) + " единиц.\n")
                if result[6] < 0:
                    for_show += ("Навык математики: " + str(-result[6]) + " единиц.\n")
                bot.send_message(message.chat.id, for_show)
        elif adding_link:
            if is_valid_link(message.text):
                cursor.execute('SELECT Links FROM Students WHERE Indexes = ?;',
                               (users_id[message.from_user.id],))

                links = cursor.fetchone()[0]
                if links.strip():
                    links = links.split(" ")
                else:
                    links = []

                links.append("0")
                links.append(message.text)
                conn.execute("UPDATE Students SET Links = ? WHERE Indexes = ?",
                             (' '.join(links), users_id[message.from_user.id]))
                conn.commit()
                bot.send_message(message.chat.id, "Ссылка успешно была добавлена!")
                adding_link = False
            else:
                bot.send_message(message.chat.id, "Ошибка. Неверно указана ссылка.")
        else:
            bot.send_message(message.chat.id, text="Ошибка. Такой команды нет.")
    elif message.from_user.id in employers_id:
        if message.text == "✉️ Отобразить портфолио":
            bot.send_message(message.chat.id, text="Укажите ФИО студента:")
            finding_student = True
        elif message.text == "Прости. Прощай.":
            employers_id.remove(message.from_user.id)
            bot.send_message(message.chat.id, text="Введите пароль:")
        elif message.text == "📇 Отфильтровать список студентов по баллам":
            bot.send_message(message.chat.id, text="Укажите нижнюю планку среднего балла:")
            averaging = True
        # Блок чистоты.
        elif averaging:
            averaging = False
            cursor.execute('SELECT Name, (Soft_Skills + Backend_Programming + '
                           'Frontend_Programming + Engineering + Construction + Design + Mathematics) / 7 '
                           'FROM Students WHERE (Soft_Skills + Backend_Programming + '
                           'Frontend_Programming + Engineering + Construction + Design + Mathematics) / 7 > ?;',
                           (float(message.text),))
            result = cursor.fetchall()
            for_show = "Подходящие студенты:\n"
            print(result)
            for i in range(len(result)):
                for_show += result[i][0] + ": " + str(result[i][1]) + " баллов.\n"
            bot.send_message(message.chat.id, text=for_show)
        elif finding_student:
            finding_student = False
            cursor.execute('SELECT * FROM Students WHERE Name = ?;', (message.text,))
            data = cursor.fetchone()
            if data is None:
                bot.send_message(message.chat.id, "Такого студента нет!")
            else:
                for_show = "Студент " + data[2] + ":\n\nСсылки на предыдущие работы студента:\n"
                if not len(data[3]):
                    for_show += "Отсутствуют.\n"
                else:
                    data2 = data[3].split(" ")
                    for i in range(len(data2)):
                        if i % 2:
                            if int(data2[i - 1]):
                                for_show += str((i - 1) // 2 + 1) + ". " + data2[i] + " оценка: " + data2[i - 1] + "\n"
                            else:
                                for_show += str((i - 1) // 2 + 1) + ". " + data2[i] + "\n"
                for_show += "\n"
                for_show += "Soft Skills: " + str(data[4]) + "\n"
                for_show += "Backend программирование: " + str(data[5]) + "\n"
                for_show += "Frontend Программирование: " + str(data[6]) + "\n"
                for_show += "Инженерные навыки: " + str(data[7]) + "\n"
                for_show += "Конструирование: " + str(data[8]) + "\n"
                for_show += "Дизайн: " + str(data[9]) + "\n"
                for_show += "Математика: " + str(data[10]) + "\n\n"
                average_mark = (data[4] + data[5] + data[6] + data[7] + data[8] + data[9] + data[10]) / 7
                for_show += "Средний балл по учебной программе: " + str(round(average_mark, 2)) + ".\n"
                for_show += "Достижения на факультативах: "
                if data[11] is not None:
                    for_show += data[11] + "."
                else:
                    for_show += "Отсутствуют."
                bot.send_message(message.chat.id, text=for_show)
        else:
            bot.send_message(message.chat.id, text="Ошибка. Такой команды нет.")


bot.polling(none_stop=True)
