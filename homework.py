import logging
import os
import random
import time

import requests
import vk_api
from dotenv import load_dotenv

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
    """Проверяет доступность переменных окружения."""
    if all([PRACTICUM_TOKEN, VK_TOKEN, VK_USER_ID]):
        return True
    logging.critical('Отсутствует обязательная переменная окружения')
    return False


def send_message(vk, message):
    """Отправляет сообщение в VK-чат пользователя."""
    try:
        vk.messages.send(
            user_id=VK_USER_ID,
            message=message,
            random_id=random.randint(1, 1000000),
        )
        logging.debug(f'Сообщение отправлено: {message}')
    except Exception as e:
        logging.error(f'Ошибка при отправке сообщения: {e}')
        raise Exception(f'Ошибка VK: {e}')


def get_api_answer(timestamp):
    """Делает запрос к API и возвращает ответ."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp},
            timeout=10,
        )
        if response.status_code != 200:
            raise Exception(
                f'API недоступно, статус код: {response.status_code}'
            )
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f'Сбой при запросе к эндпоинту {ENDPOINT}: {e}'
        logging.error(error_msg)
        raise Exception(error_msg)


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        logging.error('Ответ не является словарем')
        raise Exception('Ответ не является словарем')

    if 'homeworks' not in response:
        logging.error('Нет ключа "homeworks"')
        raise Exception('Отсутствует ключ homeworks')

    if not isinstance(response['homeworks'], list):
        logging.error('Ключ "homeworks" не является списком')
        raise Exception('homeworks должен быть списком')

    if not response['homeworks']:
        logging.debug('В ответе API нет новых статусов')

    return response


def parse_status(homework):
    """Извлекает статус из элемента списка домашних работ."""
    if 'homework_name' not in homework:
        logging.error('Отсутствует ключ "homework_name"')
        raise Exception('Нет названия работы')

    if 'status' not in homework:
        logging.error('Отсутствует ключ "status"')
        raise Exception('Нет статуса работы')

    status = homework['status']
    homework_name = homework['homework_name']

    if status not in HOMEWORK_VERDICTS:
        logging.error(f'Неизвестный статус: {status}')
        raise Exception(f'Неизвестный статус: {status}')

    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Программа остановлена')
        return

    try:
        vk_session = vk_api.VkApi(token=VK_TOKEN)
        vk = vk_session.get_api()
    except Exception as e:
        logging.critical(f'Ошибка при создании сессии VK: {e}')
        return

    timestamp = 0
    last_error = None

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            timestamp = response.get('current_date', timestamp)

            for homework in response.get('homeworks', []):
                send_message(vk, parse_status(homework))

            last_error = None

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logging.error(error_message)

            if str(error) != last_error:
                send_message(vk, error_message)
                last_error = str(error)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
