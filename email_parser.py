import imaplib
import email
import re
import requests
import os

EMAIL = "daniljk09@gmail.com"
PASSWORD = os.environ.get("GMAIL_PASSWORD", "ahae miip yiul rdkx")
API_URL = "https://jewelry-api.jewelry-api.workers.dev/api/update-rating"

# ========== НАСТРОЙКИ ==========
EMAIL_TO_SHOP = {
    "alina119.1995@mail.ru": "huy_thanh_jewelry",
    "alina_belyayeva@mail.ru": "pnj_goldcoast",
}

DISABLED_SHOPS = ["long_beach_pearl"]

SHOP_NAMES_TO_ID = {
    "long beach pearl": "long_beach_pearl",
    "huy thanh jewelry": "huy_thanh_jewelry",
    "pnj goldcoast nha trang": "pnj_goldcoast",
    "pandora gold coast nha trang": "pandora_goldcoast",
    "thế giới kim cương gold coast nha trang": "the_gioi_kim_cuong",
    "saigon pearl": "saigon_pearl",
    "kim anh jewelry": "kim_anh_jewelry",
    "hong hac jewelry store": "hong_hac_jewelry",
    "treasures of angkor": "treasures_of_angkor",
    "kim's jewellery": "kims_jewellery",
    "sjc nha trang": "sjc_nha_trang",
    "pnj da nang": "pnj_da_nang",
    "sjc da nang": "sjc_da_nang",
    "doji da nang": "doji_da_nang",
    "jemmia da nang": "jemmia_da_nang",
    "hanh hoa jewelry": "hanh_hoa_jewelry",
    "sjc phu quoc": "sjc_phu_quoc",
    "long bin jewelry": "long_bin_jewelry",
    "pnj phu quoc": "pnj_phu_quoc",
    "phu quoc pearl": "phu_quoc_pearl",
    "sjc ho chi minh": "sjc_ho_chi_minh",
    "pnj headquarters": "pnj_headquarters",
    "doji hcmc": "doji_hcmc",
    "tiffany & co. hcmc": "tiffany_hcmc",
}
# ================================================================

def parse_rating_to_float(text: str) -> float:
    match = re.search(r'(\d+[.,]?\d*)', text)
    if not match:
        return None
    raw = match.group(1).replace(',', '.')
    try:
        number = float(raw)
    except:
        return None
    
    if number > 10:
        if number >= 10000:
            number = number / 10000
        elif number >= 1000:
            number = number / 1000
        else:
            number = number / 10
    
    number = max(0, min(number, 3))
    return round(number, 3)

def normalize_shop_name(name: str) -> str:
    """Очищает название магазина от лишних символов и приводит к нижнему регистру"""
    # Убираем точку в конце, лишние пробелы
    name = name.strip().lower()
    # Убираем точку в конце, если есть
    name = name.rstrip('.')
    # Убираем множественные пробелы
    name = re.sub(r'\s+', ' ', name)
    return name

def parse_command(body: str):
    """Разбирает письмо от администратора. Формат: Магазин — рейтинг (каждый с новой строки)"""
    results = []
    lines = body.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Пробуем разные разделители: —, -, :, пробел
        found_sep = None
        for sep in [' — ', '—', ' - ', '-', ': ', ' ']:
            if sep in line:
                found_sep = sep
                break
        
        if found_sep:
            parts = line.split(found_sep, 1)
            if len(parts) == 2:
                shop_name_raw = normalize_shop_name(parts[0])
                rating_raw = parts[1].strip()
                
                # Ищем соответствие в словаре
                matched_shop_id = None
                for known_name, shop_id in SHOP_NAMES_TO_ID.items():
                    if shop_name_raw == known_name or known_name in shop_name_raw:
                        matched_shop_id = shop_id
                        break
                
                if matched_shop_id:
                    rating = parse_rating_to_float(rating_raw)
                    if rating is not None:
                        results.append((matched_shop_id, rating))
                        print(f"  Распознано: {shop_name_raw} → {matched_shop_id}, рейтинг {rating}")
                    else:
                        print(f"  Не удалось распознать рейтинг в: {rating_raw}")
                else:
                    print(f"  Не найден магазин: {shop_name_raw}")
            else:
                print(f"  Не удалось разобрать строку: {line}")
        else:
            print(f"  Нет разделителя в строке: {line}")
    
    return results

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

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() in ["text/plain", "text/html"]:
                        try:
                            payload = part.get_payload(decode=True).decode("utf-8")
                            body += payload
                        except:
                            pass
            else:
                body = msg.get_payload(decode=True).decode("utf-8")

            print(f"Тело письма: {body[:200]}...")

            # --- Письмо от администратора ---
            if sender_email == "danil-jk@bk.ru":
                print("Обработка команды от администратора")
                updates = parse_command(body)
                if not updates:
                    print("Не удалось распознать команды в письме")
                for shop_id, rating in updates:
                    if shop_id in DISABLED_SHOPS:
                        print(f"Магазин {shop_id} отключён, рейтинг не обновлён")
                        continue
                    print(f"Обновляем {shop_id} -> {rating}")
                    try:
                        response = requests.post(API_URL, json={"shopId": shop_id, "newRating": rating})
                        if response.status_code == 200:
                            print(f"✅ Рейтинг {shop_id} обновлён!")
                            mail.store(msg_id, '+FLAGS', '\\Seen')
                        else:
                            print(f"❌ Ошибка API: {response.status_code}")
                    except Exception as e:
                        print(f"Ошибка отправки: {e}")
                continue

            # --- Письмо от брокера ---
            if sender_email not in EMAIL_TO_SHOP:
                print(f"Отправитель не найден в таблице, письмо оставлено непрочитанным")
                continue

            shop_id = EMAIL_TO_SHOP[sender_email]

            if shop_id in DISABLED_SHOPS:
                print(f"Магазин {shop_id} отключён, письмо проигнорировано")
                continue

            rating = parse_rating_to_float(body)
            if rating is None:
                print(f"Число не найдено в письме")
                continue

            print(f"Найдено число → рейтинг: {rating}")

            response = requests.post(API_URL, json={"shopId": shop_id, "newRating": rating})
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
