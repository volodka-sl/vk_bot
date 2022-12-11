import requests
import json

payload = {}
headers = {
    "apikey": "4Vkp8Di6pnNx3rSgr3I7Kf5TCaOx7pUZ"
}


def get_currencies(currencies):
    final = "Топ-5 валют по популярности к рублю:\n\n"
    for currency in currencies:
        url = f"https://api.apilayer.com/currency_data/convert?to=RUB&from={currency}&amount=1"
        response = requests.request("GET", url, headers=headers, data=payload)
        result = json.loads(response.text)["result"]
        final += f"1 {currency}: {round(result, 2)}₽\n"

    return final
