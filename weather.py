import yandex_weather_api
import requests
import datetime
from geopandas.tools import geocode


def get_weather(req_city, req_day):
    city = req_city
    location = geocode(city, provider="nominatim", user_agent='my_request')
    point = location.geometry.iloc[0]
    response = yandex_weather_api.get(requests, "c795c6c6-26c2-4d09-a9d3-920c26c82552", rate="forecast",
                                      lat=point.y,
                                      lon=point.x,
                                      lang="ru_RU",
                                      limit=2,
                                      )
    now = datetime.datetime.now()
    if req_day == "сегодня":
        response_for_hour = response["forecast"][0]["hours"][now.hour]
        return f"Сейчас в городе {city} {response_for_hour['condition']}, температура {response_for_hour['temp']}°C, ощущается как {response_for_hour['feels_like']}°C."
    else:
        avg_temp_for_tommorow = int(response["forecast"][1]["parts"]["day"]["temp_avg"])
        fl_temp_for_tommorow = int(response["forecast"][1]["parts"]["day"]["feels_like"])
        condition_for_tommorow = response["forecast"][1]["parts"]["day"]["condition"]
        return f"Завтра в городе {city} {condition_for_tommorow}, температура {avg_temp_for_tommorow}°C, будет ощущаться как {fl_temp_for_tommorow}°C."
