import imaplib
import email
import re
import requests
import os

EMAIL = "daniljk09@gmail.com"
PASSWORD = os.environ.get("GMAIL_PASSWORD", "ahae miip yiul rdkx")
API_URL = "https://jewelry-api-xb0q.onrender.com/api/update-rating"

EMAIL_TO_SHOP = {
    "danil-jk@bk.ru": "long_beach_pearl",
    "alina119.1995@mail.ru": "huy_thanh_jewelry",
    "alina_belyayeva@mail.ru": "pnj_goldcoast",
}

def parse_number(text):
    """Извлекает число из текста и преобразует в рейтинг 0.000 - 3.000"""
    match = re.search(r'(\d+)', text)
    if not match:
        return None
    raw = match.group(1)
    
    # Если число больше 999, преобразуем: 234560 -> 2.34560
    if len(raw) > 3:
        number = float(raw) / 100000
    else:
        number = float(raw) / 1000
    
    # Ограничиваем от 0 до 3
    number = max(0, min(number, 3))
    return round(number, 5)

def process_emails():
    print("Подключение к Gmail...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(EMAIL, PASSWORD.replace(" ", ""))
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            print("Новых писем нет")
            mail.close()
            mail.logout()
            return

        print(f"Найдено {len(messages[0].split())} новых писем")
        for msg_id in messages[0].split():
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            from_header = msg.get("From", "")
            sender_match = re.search(r'<(.+?)>', from_header)
            sender_email = sender_match.group(1) if sender_match else from_header
            print(f"Письмо от: {sender_email}")

            if sender_email not in EMAIL_TO_SHOP:
                print(f"Отправитель не найден в таблице")
                continue

            shop_id = EMAIL_TO_SHOP[sender_email]

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() in ["text/plain", "text/html"]:
                        try:
                            body += part.get_payload(decode=True).decode("utf-8")
                        except:
                            pass
            else:
                body = msg.get_payload(decode=True).decode("utf-8")

            rating = parse_number(body)
            if rating is None:
                print(f"Число не найдено в письме")
                continue

            print(f"Найдено число → рейтинг: {rating}")

            response = requests.post(API_URL, json={"shop_id": shop_id, "new_rating": rating})
            if response.status_code == 200:
                print(f"✅ Рейтинг обновлён!")
                mail.store(msg_id, '+FLAGS', '\\Seen')
            else:
                print(f"❌ Ошибка API: {response.status_code}")

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    process_emails()
