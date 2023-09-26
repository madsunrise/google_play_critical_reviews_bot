from enum import Enum

import telebot
from google_play_scraper import reviews, Sort

from get_app_store_reviews import get_and_collect_reviews

bot = telebot.TeleBot('BOT_TOKEN')
CACHE_FOLDER = '/root/google_play_review_scrapper/cache'


@bot.message_handler(commands=['start'])
def start(message):
    first_message = "Бот умеет выгружать отрицательные отзывы как из Google Play, так и из Apple Store."
    google_play = "[Google Play]\nУкажи платформу (google), package name приложения, язык ('ru', 'en' либо другой) и количество отзывов (не более 100 тысяч). " \
                  "Будут выгружены только отрицательные отзывы (с одной звездой), от самых свежих к более старым.\n\nПримеры сообщений: " \
                  "\ngoogle com.microsoft.office.outlook en 10000" \
                  "\ngoogle com.whatsapp ru 50000"
    app_store = "[App Store]\nУкажи платформу (apple), ID приложения и код страны ('ru', 'gb' и т.д.). " \
                "Будут выгружены только отрицательные отзывы (с одной звездой) из 500 последних отзывов (RSS Feed).\n\nПримеры сообщений: " \
                "\napple 511310430 ru" \
                "\napple 722120997 gb"
    bot.send_message(message.from_user.id, first_message)
    bot.send_message(message.from_user.id, google_play)
    bot.send_message(message.from_user.id, app_store)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    parsed = message.text.split()
    platform = parsed[0]
    if platform == 'google':
        if len(parsed) != 4:
            bot.send_message(message.from_user.id, "Некорректный формат (справка: /start)")
            return
        app = parsed[1]
        lang = parsed[2]
        count = parsed[3]
        process_request(app, lang, count, message, Platform.GOOGLE)
    elif platform == 'apple':
        if len(parsed) != 3:
            bot.send_message(message.from_user.id, "Некорректный формат (справка: /start)")
            return
        app = parsed[1]
        lang = parsed[2]
        process_request(app, lang, "0", message, Platform.APPLE)
    else:
        bot.send_message(message.from_user.id, "Платформа должна быть или google, или apple (справка: /start)")


class Platform(Enum):
    APPLE = 0,
    GOOGLE = 1


def process_request(app, lang, count, message, platform):
    if not count.isnumeric():
        bot.send_message(message.from_user.id, "Некорректное количество")
        return
    countInt = int(count)
    if platform == Platform.GOOGLE and countInt > 100000:
        bot.send_message(message.from_user.id, "Слишком большое количество")
        return
    if platform == Platform.GOOGLE and countInt <= 0:
        bot.send_message(message.from_user.id, "Количество должно быть положительным")
        return
    wait_msg = f'[{platform.name}] Приложение: {app}, язык/страна: {lang}. Загрузка...\n\nОжидание составит до 5-7 минут.'
    bot.send_message(message.from_user.id, wait_msg)
    uniqueId = message.date
    try:
        file = None
        if platform == Platform.GOOGLE:
            file = fetch_reviews_google_play(app=app, lang=lang, count=countInt, uniqueId=uniqueId)
        elif platform == Platform.APPLE:
            file = fetch_reviews_app_store(app=app, country=lang, uniqueId=uniqueId)

        if file is None:
            bot.send_message(message.from_user.id, f'Отрицательные отзывы для {app} не обнаружены.')
            return

        bot.send_message(message.from_user.id, f'Отзывы для {app} загружены:')
        bot.send_document(message.from_user.id, open(file.name, 'rb'))
        file.close()
    except Exception as e:
        error_message = 'Exception occurred: ' + str(e)
        print(error_message)
        bot.send_message(message.from_user.id, error_message)


def fetch_reviews_google_play(app, lang, count, uniqueId):
    print(f'Fetching reviews from Google Play for {app}, lang={lang}')
    app_reviews = reviews(
        app,
        lang=lang,
        country='us',
        sort=Sort.NEWEST,
        filter_score_with=1,
        count=count
    )
    print(f'Fetching reviews for {app}, lang={lang} has finished')
    mapped = []
    for review in app_reviews[0]:
        username = review['userName']
        date = str(review['at'].date())
        review_text = review['content']
        review = construct_review(username, date, review_text)
        if review is not None:
            mapped.append(review)

    if not mapped:
        print('No reviews found')
        return None

    print(f'Mapped list size: {len(mapped)}')
    joined = "\n\n".join(mapped)
    file_name = f'google_{app}_{lang}_{uniqueId}.txt'
    temp = open(f'{CACHE_FOLDER}/{file_name}', "w")
    temp.write(joined)
    temp.flush()
    return temp


def construct_review(username: str, extra_info: str, text: str):
    if text is None:
        return None
    if username is None or username == '':
        if extra_info is not None:
            return extra_info + '\n' + text
        else:
            return text
    else:
        if extra_info is not None:
            return username + ' (' + extra_info + ')\n' + text
        else:
            return username + '\n' + text


def fetch_reviews_app_store(app, country, uniqueId):
    print(f'Fetching reviews from App Store for {app}, country={country}')
    num_of_pages = 10  # 10 is a maximum value for RSS
    all_reviews = get_and_collect_reviews(app, num_of_pages, country)
    bad_reviews = list(filter(lambda x: x['im_rating'] == '1', all_reviews))

    print(f'Fetching reviews for {app}, country={country} has finished')
    mapped = []
    for review in bad_reviews:
        username = review['author_name']
        version = 'version ' + review['im_version']
        review_title = review['title']
        review_text = review['content']
        review = construct_review(username, version, review_title + '\n' + review_text)
        if review is not None:
            mapped.append(review)

    if not mapped:
        print('No reviews found')
        return None

    print(f'Mapped list size: {len(mapped)}')
    joined = "\n\n".join(mapped)
    file_name = f'apple_{app}_{country}_{uniqueId}.txt'
    temp = open(f'{CACHE_FOLDER}/{file_name}', "w")
    temp.write(joined)
    temp.flush()
    return temp


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
