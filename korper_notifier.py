#!/usr/bin/env python3
"""
korper_notifier.py

Автоматичний відправник листів з CSV, з логуванням і тестовим режимом.
"""

import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import csv

# --- Конфігурація ---
ALLOWED_YEARS = [2025]
ALLOWED_MONTHS = [8, 9]  # серпень і вересень 2025
TEST_MODE = True  # True — ігнорувати перевірку дати, для тесту

# Підвантажуємо .env
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)

# --- Перевірка дати ---
today = datetime.now()

if not TEST_MODE:
    if not (today.year in ALLOWED_YEARS and today.month in ALLOWED_MONTHS):
        print(f"[INFO] Скрипт не запускається: зараз {today.year}-{today.month}, дозволено тільки серпень і вересень 2025.")
        exit()

    start_date = datetime(2025, 8, 1)
    delta_days = (today - start_date).days
    if delta_days % 3 != 0:
        print(f"[INFO] Сьогодні {today.date()} не підходить (кратність 3 не виконана).")
        exit()
else:
    print("[INFO] TEST_MODE увімкнено — перевірка дати пропущена.")

# ----- Шаблон листа -----
EMAIL_TEMPLATE = {
    "subject": "Нагадування: тренування — {date}",
    "body": (
        "Привіт, {name}!\n\n"
        "Час іти тренуватись. Сьогодні твоє завдання: підтягування.\n"
        "Поточний максимум: {current} раз(и). Мета: {target} раз(и).\n\n"
        "План на сьогодні:\n"
        "- Розминка 5-10 хв\n"
        "- 4 підходи підтягувань до відмови\n"
        "- Допоміжні вправи: австралійські підтягування, тяга в нахилі\n\n"
        "Вперед — в тебе вийде 💪\n\n"
        "Твій бот-тренер"
    )
}

# ----- Функція відправки листа -----
def send_email(smtp_host, smtp_port, username, password, to_email, subject, body, from_name="Твій тренер-бот"):
    msg = EmailMessage()
    msg["From"] = f"{from_name} <{username}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            if smtp_port == 587:
                server.starttls()
                server.ehlo()
            server.login(username, password)
            server.send_message(msg)
        print(f"[SUCCESS] Лист надіслано до {to_email}")
    except Exception as e:
        print(f"[ERROR] Не вдалося надіслати лист до {to_email}. Помилка: {e}")

# ----- Main -----
def main():
    username = os.getenv("MY_EMAIL")
    password = os.getenv("MY_PASSWORD")
    smtp_host = os.getenv("MY_SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("MY_SMTP_PORT", 587))

    if not username or not password:
        print("[ERROR] Задайте MY_EMAIL та MY_PASSWORD у файлі .env")
        return

    csv_path = Path(__file__).parent / "data.csv"
    if not csv_path.exists():
        print("[ERROR] Не знайдено CSV файл data.csv")
        return

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows_sent = 0
        for row in reader:
            name = row.get("name", "Друже")
            to_email = row.get("email")
            current = row.get("current", 0)
            target = row.get("target", 20)

            if not to_email:
                print(f"[WARN] Пропущено рядок без email: {row}")
                continue

            subject = EMAIL_TEMPLATE["subject"].format(date=datetime.now().strftime("%Y-%m-%d"))
            body = EMAIL_TEMPLATE["body"].format(name=name, current=current, target=target)

            send_email(smtp_host, smtp_port, username, password, to_email, subject, body)
            rows_sent += 1

        if rows_sent == 0:
            print("[INFO] Листи не були відправлені — немає валідних email у CSV")
        else:
            print(f"[INFO] Всього надіслано листів: {rows_sent}")

if __name__ == "__main__":
    main()
