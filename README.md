# Homework Bot VK

Бот для отслеживания статуса проверки домашних работ в Яндекс.Практикуме с отправкой уведомлений в VK.

## Установка

1. Клонируйте репозиторий:
git clone https://github.com/SelinaValer-ia/homework-bot-vk.git
cd homework-bot-vk

2. Создайте и активируйте виртуальное окружение:
python -m venv venv
source venv/bin/activate  # для Linux/MacOS
# или
venv\Scripts\activate  # для Windows

3.Установите необходимые зависимости:
pip install -r requirements.txt

## Настройка переменных окружения

Создайте файл .env в корневой директории проекта и добавьте следующие переменные:
PRACTICUM_TOKEN=your_practicum_token_here
VK_TOKEN=your_vk_token_here
VK_USER_ID=your_vk_user_id_here

Описание переменных:
PRACTICUM_TOKEN	- Токен для доступа к API Яндекс.Практикума
Пример:
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

VK_TOKEN - Токен доступа VK API	
Пример:
vk1.a.abcdefghijklmnopqrstuvwxyz...

VK_USER_ID - ID пользователя VK для отправки сообщений	
Пример:
123456789

## Как получить токены:
1.PRACTICUM_TOKEN:
Авторизуйтесь на Яндекс.Практикум
Перейдите в настройки профиля и найдите раздел API
Скопируйте токен

2.VK_TOKEN:
Перейдите на VK Developers
Создайте приложение и получите токен доступа
Подробнее: Документация VK API

3.VK_USER_ID:
Ваш числовой ID в VK (можно найти в настройках профиля или через сервисы определения ID)

## Запуск
python homework_bot.py

## Логирование
Логи работы бота сохраняются в файл program.log в корневой директории проекта.

## Требования
Python 3.7+
Библиотеки из requirements.txt