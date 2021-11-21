import random
import string
import json
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from enum import Enum
from os.path import exists
import statics.bot_token as bot_token

class States(Enum):
    MENU = 0
    ENTER_PASSNAME = 1
    ENTER_PASS_LENGTH = 2
    SEARCH_RESULT = 3

def user_file_location(userid:str):
    return "statics/"+userid+".json"

def load_from_file(userid:str):
    file_exists = exists(user_file_location(userid))
    if file_exists:
        fileObject = open(user_file_location(userid), "r")
        jsonContent = fileObject.read()
        my_dict = json.loads(jsonContent)
    else:
        my_dict={}
    return my_dict

def store_in_file(my_dict,userid : str):
    jsonString = json.dumps(my_dict)
    jsonFile = open(user_file_location(userid), "w")
    jsonFile.write(jsonString)

def listToString(s): 
    str1 = ""  
    for ele in s: 
        str1 += ele    
    return str1

def generate_password(pass_length):

    ascii_letters_length = random.randint( 3 , pass_length )
    digits_length = random.randint( 0 , ( pass_length - ascii_letters_length ) )
    punctuation_length =pass_length - ascii_letters_length - digits_length

    password = ''

    for i in range(ascii_letters_length):
        my_char = random.choice(string.ascii_letters)
        password = password + my_char
    
    for i in range(digits_length):
        my_char = random.choice(string.digits)
        password = password + my_char

    custom_chars = "?!@$%&"
    for i in range(punctuation_length):
        my_char = random.choice(custom_chars)
        password = password + my_char
    
    temp_list = list(password)
    random.shuffle(temp_list)
    password = listToString(temp_list)
    print("your random pass is : ", password)
    return password

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )
    context.user_data["passwords"] = load_from_file(str(user.id))
    return States.MENU

def print_passwords(update: Update, context: CallbackContext):
    update.message.reply_text(context.user_data["passwords"]) # --> {"Namav": "OyGFVaF9waz1"}
    return States.MENU

def add_password(update: Update, context: CallbackContext):
    update.message.reply_text('Enter your password name')
    return States.ENTER_PASSNAME
        
def get_passname(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Enter your password length')
    # print("pass name : " + update.message.text)
    context.user_data["pass_name"] = update.message.text
    return States.ENTER_PASS_LENGTH

def get_passlength(update: Update, context: CallbackContext):
    generated_password = generate_password(int(update.message.text))
    update.message.reply_text(generated_password)
    passes = context.user_data["passwords"]
    passes[context.user_data["pass_name"]] = generated_password
    context.user_data["passwords"] = passes 
    user = update.effective_user
    store_in_file(context.user_data["passwords"],str(user.id))
    return States.MENU

def stop(update: Update, context: CallbackContext) -> int:
    """End Conversation by command."""
    update.message.reply_text('Okay, bye.')

def menu(update: Update, context: CallbackContext) -> int:
    return States.MENU

def search(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Enter name for search')
    return States.SEARCH_RESULT

def search_result(update: Update, context: CallbackContext) -> int:
    name_for_search = update.message.text
    passes = context.user_data["passwords"]
    if name_for_search in passes :
        # print("the password for ",name_for_search," is : ",context.user_data["passwords"][name_for_search])
        update.message.reply_text("the password for "+name_for_search+" is : "+passes[name_for_search])
    else :
        print("password not found to add use menu!!")
        update.message.reply_text("password not found to add use menu!!")
    return States.MENU
    
def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_token.TOKEN)
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    search_handler = ConversationHandler(
        entry_points=[CommandHandler('search', search)],
        states={
            States.SEARCH_RESULT: [MessageHandler(Filters.text & ~Filters.command, search_result)],
        },
        fallbacks=[CommandHandler('menu', menu)],
        map_to_parent={
            States.MENU : States.MENU
        },
    )

    add_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_password)],
        states={
            States.ENTER_PASSNAME: [MessageHandler(Filters.text & ~Filters.command, get_passname)],
            States.ENTER_PASS_LENGTH: [MessageHandler(Filters.text & ~Filters.command, get_passlength)],
        },
        fallbacks=[CommandHandler('menu', menu)],
        map_to_parent={
            States.MENU : States.MENU
        },
    )

    menu_handlers = [
        add_handler,
        search_handler,
        CommandHandler('print', print_passwords),
        CommandHandler('stop', stop),
    ]
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            States.MENU: menu_handlers
        },
        fallbacks=[CommandHandler('stop', stop)],
    )
    # on different commands - answer in Telegram
    dispatcher.add_handler(conv_handler)
    # dispatcher.add_handler(CommandHandler("add", get_passname))

    # on non command i.e message - echo the message on Telegram
    # dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, text_inputs))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()