import logging
import os
import random
import time

import requests
import vk_api
from dotenv import load_dotenv


class ApiRequestError(Exception):
    """Ошибка запроса к API."""


class ApiStatusError(Exception):
    """Ошибка: API вернул не 200."""


class ResponseFormatError(TypeError):
    """Ошибка формата ответа API."""


class UnknownStatusError(Exception):
    """Ошибка: неизвестный статус работы."""


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
VK_TOKEN = os.getenv('VK_TOKEN')
VK_USER_ID = os.getenv('VK_USER_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def check_tokens():
    """Проверяет наличие переменных окружения."""
    missing = []
    if not PRACTICUM_TOKEN:
        missing.append('PRACTICUM_TOKEN')
    if not VK_TOKEN:
        missing.append('VK_TOKEN')
    if not VK_USER_ID:
        missing.append('VK_USER_ID')
    return missing


def send_message(vk, message):
    """Отправляет сообщение в VK."""
    try:
        vk.messages.send(
            user_id=VK_USER_ID,
            message=message,
            random_id=random.randint(1, 1000000),
        )
    except (vk_api.exceptions.ApiError,
            requests.exceptions.RequestException) as e:
        logging.error(f'Ошибка при отправке сообщения: {e}')
        raise
    else:
        logging.debug(f'Сообщение отправлено: {message[:50]}...')


def get_api_answer(timestamp):
    """Делает запрос к API и возвращает ответ."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp},
            timeout=10,
        )
        logging.debug('Отправили запрос к API')
    except requests.exceptions.RequestException as e:
        raise ApiRequestError(f'Сбой при запросе к эндпоинту {ENDPOINT}: {e}')

    if response.status_code != 200:
        raise ApiStatusError(
            f'API недоступно, статус код: {response.status_code}'
        )

    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие ожидаемой структуре."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарем')

    if 'homeworks' not in response:
        raise TypeError('В ответе API отсутствует ключ "homeworks"')

    if not isinstance(response['homeworks'], list):
        raise TypeError('Ключ "homeworks" не является списком')

    return response


def parse_status(homework):
    """Извлекает статус работы и формирует текст сообщения."""
    if 'homework_name' not in homework:
        raise ResponseFormatError(
            'В ответе API отсутствует ключ "homework_name"'
        )

    if 'status' not in homework:
        raise ResponseFormatError('В ответе API отсутствует ключ "status"')

    homework_name = homework['homework_name']
    status = homework['status']

    if status not in HOMEWORK_VERDICTS:
        raise UnknownStatusError(f'Неизвестный статус работы: {status}')

    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    missing_tokens = check_tokens()
    if missing_tokens:
        logging.critical(
            f'Отсутствуют переменные окружения: {", ".join(missing_tokens)}'
        )
        return

    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
    except Exception as e:
        logging.critical(f'Ошибка при создании сессии VK: {e}')
        return

    logging.info('Бот успешно запущен')

    last_sent_message = None
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)

            homeworks = response.get('homeworks', [])

            if homeworks:
                last_homework = homeworks[-1]
                text = parse_status(last_homework)

                if text != last_sent_message:
                    try:
                        send_message(vk, text)
                        last_sent_message = text
                        logging.info(f'Отправлен новый статус: {text}...')
                    except Exception:
                        logging.error('Ошибка отправки, статус не обновлён')
            else:
                no_changes_message = 'Нет новых статусов'
                if no_changes_message != last_sent_message:
                    try:
                        send_message(vk, no_changes_message)
                        last_sent_message = no_changes_message
                        logging.debug(
                            'Отправлено сообщение об отсутствии изменений'
                        )
                    except Exception:
                        logging.error('Сбой отправки статуса')

        except Exception as e:
            error_message = f'Ошибка: {e}'
            logging.error(error_message)
            send_message(vk, error_message)

        else:
            timestamp = response.get('current_date', timestamp)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        filename='program.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
