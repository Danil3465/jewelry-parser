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
    """Извлекает число и преобразует в рейтинг 0.000 - 3.000.
       Если число больше 3.0 — возвращает None (некорректный рейтинг)"""
    # Ищем последовательность цифр
    match = re.search(r'(\d+)', text)
    if not match:
        return None
    
    raw = match.group(1)
    
    # Если цифр меньше двух — не можем определить
    if len(raw) < 2:
        return None
    
    # Первая цифра — целая часть
    integer_part = raw[0]
    
    # Берём следующие цифры для округления до 3 знаков
    decimal_raw = raw[1:5]  # до 4 цифр для правильного округления
    
    if len(decimal_raw) >= 4:
        first_three = int(decimal_raw[:3])
        fourth = int(decimal_raw[3])
        
        if fourth >= 5:
            first_three += 1
            if first_three == 1000:
                first_three = 0
                integer_part = str(int(integer_part) + 1)
        
        decimal_part = str(first_three).zfill(3)
    else:
        decimal_part = decimal_raw.ljust(3, '0')
    
    rating_str = f"{integer_part}.{decimal_part}"
    
    try:
        rating = float(rating_str)
    except:
        return None
    
    # Если рейтинг больше 3.0 — считаем ошибочным
    if rating > 3.0:
        return None
    
    if rating < 0:
        rating = 0.0
    
    return round(rating, 3)

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
                print(f"Число не найдено или рейтинг > 3.0")
                continue

            print(f"Найдено число → рейтинг: {rating}")

            response = requests.post(API_URL, json={"shop_id": shop_id, "new_rating": rating})
            if response.status_code == 200:
                resp_data = response.json()
                if resp_data.get("status") == "error":
                    print(f"⚠️ API отклонил обновление: {resp_data.get('reason')}")
                else:
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
