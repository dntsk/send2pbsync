import os
import shutil
import zipfile
import imaplib
import smtplib
import email
from email import policy
from email.parser import BytesParser
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение данных из переменных окружения
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_USER = os.getenv('IMAP_USER')
IMAP_PASSWORD = os.getenv('IMAP_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', None)
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', None)
SEND_TO_EMAIL = os.getenv('SEND_TO_EMAIL')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', SMTP_USER)  # Указываем FROM или берем из логина по умолчанию

def connect_to_imap():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(IMAP_USER, IMAP_PASSWORD)
        logger.info("Успешное подключение к IMAP серверу.")
        return mail
    except Exception as e:
        logger.error(f"Ошибка при подключении к IMAP серверу: {e}")
        raise

def fetch_emails_by_subject(mail, subject):
    try:
        mail.select('inbox')
        result, data = mail.search(None, f'SUBJECT "{subject}"')
        if result != 'OK':
            logger.error("Ошибка при поиске писем")
            return []
        logger.info(f"Найдено писем: {len(data[0].split())}")
        return data[0].split()
    except Exception as e:
        logger.error(f"Ошибка при поиске писем: {e}")
        return []

def fetch_raw_email(mail, email_id):
    """Получить сырые данные письма с учетом всех возможных форматов."""
    try:
        result, data = mail.fetch(email_id, '(BODY.PEEK[])')
        if result != 'OK':
            logger.error(f"Ошибка получения письма с ID {email_id}: результат {result}")
            return None
        if not data:
            logger.error(f"Нет данных для письма с ID {email_id}")
            return None

        for response_part in data:
            if isinstance(response_part, tuple) and response_part[1]:
                logger.info(f"Получены данные письма с ID {email_id}: {len(response_part[1])} байт")
                return response_part[1]

        logger.error(f"Не удалось найти корректные данные для письма с ID {email_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при извлечении письма с ID {email_id}: {e}")
        return None

def download_attachments(msg, save_dir):
    attachments = []
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment' and part.get_filename() and part.get_filename().lower().endswith('.epub'):
            filename = part.get_filename()
            file_path = os.path.join(save_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(part.get_payload(decode=True))
            attachments.append(file_path)
            logger.info(f"Скачан файл: {filename}")
    return attachments

def delete_email(mail, email_id):
    try:
        mail.store(email_id, '+FLAGS', '\\Deleted')
        mail.expunge()
        logger.info(f"Письмо с ID {email_id} удалено.")
    except Exception as e:
        logger.error(f"Ошибка при удалении письма с ID {email_id}: {e}")

def create_zip(attachments, zip_name):
    try:
        with zipfile.ZipFile(zip_name, 'w') as zipf:
            for attachment in attachments:
                zipf.write(attachment, os.path.basename(attachment))
        logger.info(f"Создан ZIP архив: {zip_name}")
    except Exception as e:
        logger.error(f"Ошибка при создании ZIP архива: {e}")
        raise

def send_email_with_attachment(zip_file, to_address):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_FROM_EMAIL  # Используем значение из переменной окружения
        msg['To'] = to_address
        msg['Subject'] = 'ePub Files'

        body = 'Вложение содержит epub файлы в архиве.'
        msg.attach(MIMEText(body, 'plain'))

        with open(zip_file, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(zip_file)}')
            msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        if SMTP_USE_TLS:
            server.starttls()

        if SMTP_USER is not None and SMTP_PASSWORD is not None:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, to_address, msg.as_string())
        server.quit()
        logger.info(f"Письмо с вложением отправлено на {to_address}")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма: {e}")
        raise

def main():
    try:
        # Подключение к IMAP серверу
        mail = connect_to_imap()

        # Поиск писем по теме
        email_ids = fetch_emails_by_subject(mail, "Send to eReader")

        if not email_ids:
            logger.info("Письма не найдены.")
            return

        # Создание временной директории для сохранения вложений
        temp_dir = 'temp_attachments'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        all_attachments = []

        for email_id in email_ids:
            raw_email = fetch_raw_email(mail, email_id)
            if not raw_email:
                continue

            try:
                msg = BytesParser(policy=policy.default).parsebytes(raw_email)
            except Exception as e:
                logger.error(f"Ошибка при парсинге письма с ID {email_id}: {str(e)}")
                continue

            # Скачиваем вложения
            attachments = download_attachments(msg, temp_dir)
            all_attachments.extend(attachments)

            # Удаляем письмо
            delete_email(mail, email_id)

        if not all_attachments:
            logger.info("Нет вложений для обработки.")
            shutil.rmtree(temp_dir)
            return

        # Создание ZIP архива
        zip_file = 'epubs.zip'
        create_zip(all_attachments, zip_file)

        # Отправка нового email с ZIP архивом
        send_email_with_attachment(zip_file, SEND_TO_EMAIL)

        # Очистка временных файлов
        shutil.rmtree(temp_dir)
        os.remove(zip_file)

        # Завершение соединения с IMAP сервером
        mail.logout()
        logger.info("Скрипт завершил работу успешно.")

    except Exception as e:
        logger.error(f"Ошибка в основном цикле: {e}")

if __name__ == "__main__":
    main()
