import telebot
from google_play_scraper import reviews, Sort

bot = telebot.TeleBot('BOT_TOKEN')


@bot.message_handler(commands=['start'])
def start(message):
    msg = "Укажи package name приложения, язык ('ru', 'en' либо другой) и количество отзывов (не более 100 тысяч)." \
          "Будут выгружены только отрицательные отзывы (с одной звездой), от самых свежих к более старым. Примеры сообщений:"
    bot.send_message(message.from_user.id, msg)
    bot.send_message(message.from_user.id, "com.microsoft.office.outlook en 10000")
    bot.send_message(message.from_user.id, "com.whatsapp 50000")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    parsed = message.text.split()
    if len(parsed) != 3:
        bot.send_message(message.from_user.id, "Некорректный формат")
        return
    app = parsed[0]
    lang = parsed[1]
    count = parsed[2]
    if not count.isnumeric():
        bot.send_message(message.from_user.id, "Некорректное количество")
        return
    countInt = int(count)
    if countInt > 100000:
        bot.send_message(message.from_user.id, "Слишком большое количество: лучше поменьше")
        return
    if countInt <= 0:
        bot.send_message(message.from_user.id, "Количество должно быть положительным")
        return
    wait_msg = f'Приложение: {app}, язык: {lang}, кол-во отзывов: {count}. Загрузка...\n\nОжидание составит до 5-7 минут.'
    bot.send_message(message.from_user.id, wait_msg)
    uniqueId = message.date
    try:
        file = fetch_reviews(app=app, lang=lang, count=countInt, uniqueId=uniqueId)
        bot.send_message(message.from_user.id, f'Отзывы для {app} загружены:')
        bot.send_document(message.from_user.id, open(file.name, 'rb'))
        file.close()
    except Exception as e:
        error_message = 'Exception occurred: ' + str(e)
        print(error_message)
        bot.send_message(message.from_user.id, error_message)


def fetch_reviews(app, lang, count, uniqueId):
    print(f'Fetching reviews for {app}, lang={lang}')
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
        user_name = review['userName']
        date = str(review['at'].date())
        review_text = review['content']
        if review_text is None:
            continue
        if user_name is None or user_name == '':
            if date is not None:
                new_value = date + '\n' + review_text
            else:
                new_value = review_text
        else:
            if date is not None:
                new_value = user_name + ' (' + date + ')\n' + review_text
            else:
                new_value = user_name + '\n' + review_text
        mapped.append(new_value)
    print(f'Mapped list size: {len(mapped)}')
    joined = "\n\n".join(mapped)
    file_name = f'{app}_{lang}_{uniqueId}.txt'
    temp = open(f'/root/google_play_review_scrapper/cache/{file_name}', "w")
    temp.write(joined)
    temp.flush()
    print("File created")
    return temp


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

