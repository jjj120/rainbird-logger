import requests


def send_notification(message: str, chat_id: str, token: str) -> dict:
    url: str = "https://api.telegram.org/bot" + token + "/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
    }

    response = requests.post(url, data=data)
    return response.json()


if __name__ == "__main__":
    send_notification("Hello, world!")
