import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from currency import get_currencies
import datetime
from googlesheets_db import GoogleSpreadsheet
from geopandas.tools import geocode
from weather import get_weather

token = "vk1.a.8XlnsTJqve641NOfuAk8aJCO_IUlwTAzDmsaLXGh7rURrC7XJF6yPztIf03bxDpk7sFjTgaYzpb-XRCXB7UAvTXMPav4u3yMAiqraUxf_r6lqZvKj-UgzR2Pso21yjRmeMxdT7_IC6gCaQpqP5nTr64qAmvkCww6YsvfARerjkqi7DzH2t6i5eZZuxgJbN6DIOoqJ5ffWXVF_z16TIeIUg"

session = vk_api.VkApi(token=token)
ss_db = GoogleSpreadsheet("vk_bot_db", "creds.json")


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
    today = str(datetime.datetime.today()).split(" ")[0]
    tomorrow = str(datetime.date.today() + datetime.timedelta(days=1)).split(" ")[0]
    user_path = []
    found_city = ""
    for event in VkLongPoll(session).listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = str(event.user_id)
            user_info = session.method('users.get', {"user_ids": user_id, "fields": "city"})[0]
            id_list = ss_db.get_all_users_ids("users")
            user_name = user_info["first_name"]
            user_surname = user_info["last_name"]

            if str(user_id) in id_list:
                user_city = ss_db.get_user_city("users", user_id)
            else:
                user_city = user_info["city"]["title"] if "city" in user_info.keys() else ""
            msg = event.text.lower()

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

            agree_keyboard = VkKeyboard(one_time=True)
            agree_keyboard.add_button("Да", VkKeyboardColor.POSITIVE)
            agree_keyboard.add_button("Нет", VkKeyboardColor.NEGATIVE)

            if msg == "начать":
                if user_id in id_list:
                    user_city = ss_db.get_user_city("users", user_id)
                    write_msg(user_id, "Привет!\n\nА я тебя помню! вот, что я умею :)", main_keyboard)
                else:
                    if user_city:
                        write_msg(user_id, f"Добро пожаловать! Подскажи, {user_city} -- твой город?",
                                  agree_keyboard)
                    else:
                        user_path.append("choose_city")
                        write_msg(user_id, "Добро пожаловать! Подскажи, в каком городе ты проживаешь?")

            elif msg == "да":
                if user_id not in id_list:
                    ss_db.add_user("users", user_name, user_surname, user_id, user_city)
                else:
                    ss_db.change_user_city("users", user_id, found_city)
                write_msg(user_id, f"Отлично! Вот, что я умею :)", main_keyboard)

            elif msg == "нет":
                user_path.append("choose_city")
                write_msg(user_id, f"Хм, а где же тогда ты проживаешь?", return_keyboard)
                user_path.append("choose_city")

            elif msg == "назад":
                write_msg(user_id, "Возвращаемся...", main_keyboard)
                user_path = []

            elif "choose_city" in user_path:
                try:
                    location = geocode(event.text, provider="nominatim", user_agent='my_request')
                    found_city = location.address[0].split(",")[0]
                    write_msg(user_id, f"Правильно ли я понимаю, что твой город -- {found_city}?", agree_keyboard)
                    user_path = []
                except AttributeError:
                    write_msg(user_id, "Что-то не похоже на город... Попробуй ввести его ещё раз)", return_keyboard)

            elif msg == 'погода':
                user_path.append("weather")
                write_msg(user_id, f"Выбери, пожалуйста, желаемый день недели)", choose_days_keyboard)

            elif "weather" in user_path:
                write_msg(user_id, get_weather(user_city, msg), main_keyboard)
                user_path = []

            elif msg == 'афиша':
                user_path.append("posters")
                write_msg(user_id, f"Выбери, пожалуйста, желаемый день недели)", choose_days_keyboard)

            elif "posters" in user_path:
                if msg == "сегодня":
                    posters = ss_db.get_top_posters("posters", today, user_city)
                elif msg == "завтра":
                    posters = ss_db.get_top_posters("posters", tomorrow, user_city)

                write_msg(user_id, posters, main_keyboard)
                user_path = []

            elif msg == 'пробка':
                traffic_jam_score = ss_db.get_traffic_jam_stats("traffic_jam", user_city)
                write_msg(user_id, traffic_jam_score, main_keyboard)

            elif msg == "валюта":
                write_msg(user_id, get_currencies(("USD", "EUR", "CNY", "AED", "AUD")), main_keyboard)

            elif msg == "сменить город":
                user_path.append("choose_city")
                write_msg(user_id, "Ой, ты переехал? Тогда вводи скорее свой новый город!", return_keyboard)

            else:
                write_msg(user_id, "Я тебя не понимаю... Попробуй нажать на эту кнопку)", start_keyboard)


if __name__ == "__main__":
    main()
