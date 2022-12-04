import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from database import Database
import datetime

today = str(datetime.date.today()).split()[0]
tomorrow = datetime.date.today() + datetime.timedelta(days=1)

token = 'vk1.a.QXP_OrTEVN8DDcRLlMJh99Y4xEOFf1aJe8MyoKD-iQ1HGfAG3NXz7y0MdtilT-ke4gYpSVapjLbjYOgZF6ZTwZbUVHs6vvokM2XEk2Bik9FtMGrcsZzWklWFYZmrv9vhnHg416fulnUbYOvlh1h59pAO1QE2CUMcIw2kLnfl_cS4UaLfoypl4Cr4S7twUnfbot-FHWtyX9Uf_JFIOoZsXg'

session = vk_api.VkApi(token=token)
db = Database()


def write_msg(user_id, msg, keyboard=None):
    data = {
        "user_id": user_id,
        "message": msg,
        "random_id": get_random_id(),
    }

    if keyboard:
        data["keyboard"] = keyboard.get_keyboard()

    session.method('messages.send', data)


def main():
    user_path = []
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            users_id = db.select("SELECT id FROM users")
            if len(users_id) > 1:
                id_list = [i["id"] for i in users_id]
            else:
                id_list = [users_id["id"]]

            user_id = event.user_id
            user_info = session.method('users.get', {"user_ids": user_id, "fields": "city"})[0]

            if str(user_id) in id_list:
                user_city = db.select(f"SELECT * FROM users WHERE id='{user_id}'")["city"]
            else:
                user_city = user_info["city"]["title"] if "city" in user_info.keys() else ""
            user_data = {'id': f'{user_id}'}
            msg = event.text.lower()
            users_db = db.select("SELECT id FROM users")

            start_keyboard = VkKeyboard(one_time=True)
            start_keyboard.add_button("Начать", VkKeyboardColor.PRIMARY)

            return_keyboard = VkKeyboard(one_time=True)
            return_keyboard.add_button("Назад", VkKeyboardColor.NEGATIVE)

            main_keyboard = VkKeyboard(one_time=True)
            bot_capabilities = ("Погода", "Пробка", "Афиша", "Валюта")
            for capability in bot_capabilities:
                main_keyboard.add_button(capability, VkKeyboardColor.PRIMARY)
            main_keyboard.add_line()
            main_keyboard.add_button("Сменить город", VkKeyboardColor.POSITIVE)

            choose_days_keyboard = VkKeyboard(one_time=True)
            for day in ("Сегодня", "Завтра"):
                choose_days_keyboard.add_button(day, VkKeyboardColor.PRIMARY)
            choose_days_keyboard.add_line()
            choose_days_keyboard.add_button("Назад", VkKeyboardColor.NEGATIVE)

            if msg == "начать":
                if len(users_db) == 1:
                    user_reg_condition = user_data == users_db
                    users_db = list(users_db)
                else:
                    user_reg_condition = user_data in users_db
                if user_reg_condition:
                    user_city = db.select(f"SELECT city FROM users WHERE id='{user_id}'")['city']
                    print(user_city)
                    write_msg(user_id, "Привет!\n\nА я тебя помню! вот, что я умею :)", main_keyboard)
                else:
                    if user_city:
                        choose_city_keyboard = VkKeyboard(one_time=True)
                        choose_city_keyboard.add_button("Да", VkKeyboardColor.POSITIVE)
                        choose_city_keyboard.add_button("Нет", VkKeyboardColor.NEGATIVE)
                        write_msg(user_id, f"Добро пожаловать! Подскажи, {user_city} -- твой город?",
                                  choose_city_keyboard)
                    else:
                        user_path.append("choose_city")
                        write_msg(user_id, "Добро пожаловать! Подскажи, в каком городе ты проживаешь?")

            elif msg == "да":
                write_msg(user_id, f"Отлично! Вот, что я умею :)", main_keyboard)
                db.insert(f"INSERT INTO users VALUES ('{user_id}', '{user_city}')")

            elif msg == "нет":
                user_path.append("choose_city")
                write_msg(user_id, f"Хм, не угадал... Где же тогда ты проживаешь?")
                user_path.append("choose_city")

            elif msg == "назад":
                write_msg(user_id, "Возвращаемся...", main_keyboard)
                user_path = []

            elif "choose_city" in user_path:
                if str(user_id) in id_list:
                    db.insert(f"UPDATE users SET city='{event.text}' WHERE id='{user_id}'")
                    user_city = event.text
                else:
                    db.insert(f"INSERT INTO users VALUES ('{user_id}', '{event.text}')")
                    user_city = event.text
                write_msg(user_id, f"Отлично! Запомню, что твой город -- {event.text}! Вот мои возможности:)",
                          main_keyboard)
                user_path = []

            elif msg == 'погода':
                user_path.append("weather")
                write_msg(user_id, f"Выбери, пожалуйста, желаемый день недели)", choose_days_keyboard)

            elif "weather" in user_path:
                weather = db.select(f"SELECT * FROM weather WHERE city = '{user_city}'")
                if weather:
                    if msg == "сегодня":
                        write_msg(user_id, f"{weather['weather_today']}", main_keyboard)
                    elif msg == "завтра":
                        write_msg(user_id, f"{weather['weather_tomorrow']}", main_keyboard)
                else:
                    write_msg(user_id, "Похоже, на твой город нет прогноза :(", main_keyboard)
                user_path = []

            elif msg == 'афиша':
                user_path.append("posters")
                write_msg(user_id, f"Выбери, пожалуйста, желаемый день недели)", choose_days_keyboard)

            elif "posters" in user_path:
                if msg == "сегодня":
                    posters = db.select(
                        f"SELECT * FROM posters WHERE city = '{user_city}' AND show_date::date = '{today}'")
                elif msg == "завтра":
                    posters = db.select(
                        f"SELECT * FROM posters WHERE city = '{user_city}' AND show_date::date = '{tomorrow}'")
                sorted_posters = sorted(posters, key=lambda x: 10 - x["rating"])
                best_posters = ""
                max_posters = 5 if len(sorted_posters) > 4 else len(sorted_posters)
                for i in range(max_posters):
                    best_posters += f"Название: {sorted_posters[i]['name']}\nЦена: {sorted_posters[i]['price']}\nСсылка: {sorted_posters[i]['link']}\n\n"
                user_path = []
                if best_posters:
                    write_msg(user_id, best_posters, main_keyboard)
                else:
                    write_msg(user_id, "Похоже, в твоём городе нет афиш(", main_keyboard)

            elif msg == 'пробка':
                print(user_city)
                traffic_jam_score = db.select(f"SELECT * FROM traffic_jam WHERE city = '{user_city}'")
                if traffic_jam_score:
                    write_msg(user_id,
                              f"В городе {user_city} пробки сейчас оцениваются в {traffic_jam_score['tj_score']} баллов",
                              main_keyboard)
                else:
                    write_msg(user_id, "Похоже, по нагруженности твоего города нет информации :(", main_keyboard)

            elif msg == "валюта":
                currency = db.select(
                    "SELECT * FROM currency")  # подразумевается, что таблицы с валютами уже содержит ТОЛЬКО необходимые валюты, то есть 5 штук
                currency_to_user = ""
                for curr in currency:
                    currency_to_user += f"{curr['name']}: {curr['price_in_rubles']} рубля\n"
                write_msg(user_id, currency_to_user, main_keyboard)

            elif msg == "сменить город":
                user_path.append("choose_city")
                write_msg(user_id, "Ой, ты переехал? Тогда вводи скорее свой новый город!", return_keyboard)

            else:
                write_msg(user_id, "Я тебя не понимаю... Попробуй нажать на эту кнопку)", start_keyboard)


if __name__ == "__main__":
    main()
