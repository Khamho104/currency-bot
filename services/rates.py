import requests

API_KEY = "6f899390a85aeaf923b3e9a7"

def get_rate(from_currency, to_currency):
    try:
        url = (
            f"https://v6.exchangerate-api.com/v6/"
            f"{API_KEY}/pair/{from_currency}/{to_currency}"
        )

        response = requests.get(url)
        data = response.json()

        if data["result"] == "success":
            return data["conversion_rate"]

        return None

    except Exception as e:
        print("Ошибка:", e)
        return None