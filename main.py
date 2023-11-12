from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import http.client
import json

TOKEN = "YOUR_BOT_TOKEN"
API_KEY = "YOUR_API_KEY"
API_HOST = "api.collectapi.com"

user_requests = {}


def get_weather(city, lang='tr'):
    conn = http.client.HTTPSConnection(API_HOST)

    headers = {
        'content-type': "application/json",
        'authorization': f"apikey {API_KEY}"
    }

    endpoint = f"/weather/getWeather?data.lang={lang}&data.city={city}"
    conn.request("GET", endpoint, headers=headers)

    res = conn.getresponse()
    data = res.read().decode("utf-8")
    weather_data = json.loads(data)

    return weather_data["result"]


def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text="Welcome, his bot was created for weather forecasting.")
    create_user(chat_id)


def create_user(chat_id):
    user_file = f"users/{chat_id}.txt"

    try:
        with open(user_file, "x"):
            pass
    except FileExistsError:
        print(f"{user_file} already exists. It couldn't be created.")


def weather(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    with open(f'users/{chat_id}.txt', 'r') as user_file:
        user_cities = [line.strip() for line in user_file]
    lang = "tr"

    if not user_cities:
        context.bot.send_message(chat_id=chat_id, text="You should add a city first.")

    else:
        for city in user_cities:
            weather_data = get_weather(city, lang)

            if weather_data:
                message = f"Weather forecast for {city}:\n"
                for day in weather_data:
                    message += f"{day['date']} ({day['day']}): {day['description']}, {day['degree']}°C\n"

                context.bot.send_message(chat_id=chat_id, text=message)
            else:
                context.bot.send_message(chat_id=chat_id, text="Failed to retrieve data.")


def delete_city(update, context):
    chat_id = update.effective_chat.id
    user_requests[chat_id] = "delete"

    with open(f"users/{chat_id}.txt", 'r+') as user_file:
        user_cities = [line.strip() for line in user_file]

        if user_cities:
            message = "Enter the city you want to delete using only English characters. "
            message += "Here are the registered cities:\n"
            for user_city in user_cities:
                message += user_city + "\n"
            context.bot.send_message(chat_id=chat_id, text=message)
        else:
            context.bot.send_message(chat_id=chat_id, text="You haven't added any cities yet.")


def add_city(update, context):
    chat_id = update.effective_chat.id
    user_requests[chat_id] = "add"
    context.bot.send_message(chat_id=chat_id, text="Enter the city you live in using only English characters, "
                                                   "for example, eskisehir.")


def handle_city(update, context):
    chat_id = update.effective_chat.id
    city = update.message.text.lower()

    if chat_id in user_requests and user_requests[chat_id] == "add":

        with open(f"users/{chat_id}.txt", 'r+') as user_file:
            user_city = [line.strip() for line in user_file]

            if city in user_city:
                context.bot.send_message(chat_id=chat_id, text="This city is already registered.")
            else:
                user_file.write(str(city) + "\n")
                context.bot.send_message(chat_id=chat_id, text=f"{city} added to your city list.")

            del user_requests[chat_id]

    elif chat_id in user_requests and user_requests[chat_id] == "delete":

        with open(f"users/{chat_id}.txt", 'r+') as user_file:
            user_cities = [line.strip() for line in user_file]

            if city not in user_cities:
                context.bot.send_message(chat_id=chat_id, text="This city is not registered.")
            else:

                user_cities.remove(city)
                user_file.seek(0)
                user_file.truncate()

                for user_city in user_cities:
                    user_file.write(f"{user_city}\n")

                context.bot.send_message(chat_id=chat_id, text=f"{city} has been deleted from your city list.")

            del user_requests[chat_id]


def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("weather", weather, pass_args=True))
    dp.add_handler(CommandHandler("add_city", add_city))
    dp.add_handler(CommandHandler("delete_city", delete_city))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_city))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
