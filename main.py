import telebot
from google_play_scraper import reviews, Sort

bot = telebot.TeleBot('BOT_TOKEN')


@bot.message_handler(commands=['start'])
def start(message):
    msg = "Укажи package name приложения, язык ('ru', 'en' либо другой) и количество отзывов. Количество может варьироваться, чем оно больше, тем дольше ждать. Какая верхяя граница – неизвестно. " \
          "Будут выгружены только отрицательные отзывы (с одной звездой), от самых свежих к более старым. Примеры сообщений:"
    bot.send_message(message.from_user.id, msg)
    bot.send_message(message.from_user.id, "ru.mail.mailapp ru 10000")
    bot.send_message(message.from_user.id, "com.microsoft.office.outlook en 10000")

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
    bot.send_message(message.from_user.id, f'Приложение: {app}, язык: {lang}, кол-во отзывов: {count}. Загрузка...')
    uniqueId = message.date
    file = fetch_reviews(app=app, lang=lang, count=int(count), uniqueId=uniqueId)
    bot.send_message(message.from_user.id, f'Отзывы для {app} загружены:')
    bot.send_document(message.from_user.id, open(file.name, 'rb'))
    file.close()


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
    mapped = list(map(lambda x: x['userName'] + ' (' + str(x['at'].date()) + ')\n' + x['content'], app_reviews[0]))
    without_none = list(filter(lambda x: x is not None, mapped))
    joined = "\n\n".join(without_none)
    file_name = f'{app}_{lang}_{uniqueId}.txt'
    temp = open(f'/root/google_play_review_scrapper/cache/{file_name}', "w")
    temp.write(joined)
    temp.flush()
    print("File created")
    return temp


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)

