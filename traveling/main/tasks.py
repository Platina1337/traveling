import requests
from django.conf import settings


def send_sms_task(to, message):
    api_key = settings.SMSRU_API_KEY
    from_ = settings.SMSRU_FROM
    url = f"https://sms.ru/sms/send?api_id={api_key}&to={to}&msg={message}&json=1"

    if from_:
        url += f"&from={from_}"

    response = requests.get(url)
    return response.json()