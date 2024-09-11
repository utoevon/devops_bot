import logging
import re
import paramiko
import os
import subprocess
import psycopg2
from psycopg2 import Error

from telegram import Update, ForceReply
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)
from dotenv import load_dotenv


COMMANDS = {
    "get_release": "cat /etc/*-release",
    "get_uname": "uname -a && echo 'Hostname: ' &&  hostname",
    "get_uptime": "uptime",
    "get_df": "df -h",
    "get_free": "free -h",
    "get_mpstat": "mpstat",
    "get_w": "w",
    "get_auths": "last -n 10",
    "get_critical": "journalctl -q -p 2 -n 5",
    "get_ps": "ps",
    "get_ss": "ss",
    "get_apt_list": "apt list --installed",
    "get_dpkg_package": "dpkg --list | grep {}",
    "get_services": "systemctl list-units --type service",
    "get_repl_logs": "cat /var/log/postgresql/postgresql.log | grep -P 'repl_user'",
}

SQL_QUERIES = {
    "select": "SELECT * FROM {table};",
    "insert": "INSERT INTO {table}({column}) VALUES ('{value}');",
}
# Подключаем логирование
logging.basicConfig(
    filename="logfile.txt",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f"Привет {user.full_name}!")


def helpCommand(update: Update, context):
    update.message.reply_text("Test")


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text("Введите текст для поиска телефонных номеров: ")
    logging.debug("Запрос ввода текста с телефонами")
    return "findPhoneNumbers"


def findPhoneNumbers(update: Update, context):
    user_input = update.message.text
    logging.debug("User input: {}".format(user_input))
    # Получаем текст, содержащий(или нет) номера телефонов
    # Шаблон для случаев: (+7) 8XXXXXXXXXX, 8(XXX)XXXXXXX, 8 XXX XXX XX XX, 8 (XXX) XXX XX XX, 8-XXX-XXX-XX-XX
    phoneNumRegex = re.compile(
        r"(?:8|\+7)(?:(?:\d{3}| \d{3} |\(\d{3}\)| \(\d{3}\) |-\d{3}-)(?:\d{7}|\d{3}-\d{2}-\d{2}|\d{3} \d{2} \d{2}))"
    )

    phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов
    logging.debug("Результат обработки шаблоном: {}".format(phoneNumberList))

    if not phoneNumberList:  # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text("Телефонные номера не найдены")
        logging.debug("Телефонные номера не найдены")
        return  # Завершаем выполнение функции
    context.user_data["phone_list"] = phoneNumberList

    phoneNumbers = ""  # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f"{i+1}. {phoneNumberList[i]}\n"  # Записываем очередной номер

    update.message.reply_text(phoneNumbers)  # Отправляем сообщение пользователю
    logging.debug("результат обработки запроса {}".format(phoneNumberList))

    update.message.reply_text("Добавить найденные записи в базу данных? (Y/N)")
    return "addPhoneNumbers"


def addPhoneNumbers(update: Update, context):
    count = 0
    user_input = update.message.text
    yesRegex = re.compile(r"^Y$")
    noRegex = re.compile(r"^N$")
    list = context.user_data.get("phone_list", "Not found")
    if yesRegex.search(user_input):
        for i in range(len(list)):
            count = count + connectDBAndInsertQuery(
                SQL_QUERIES["insert"].format(
                    table="phones", column="phone", value=list[i]
                )
            )
        update.message.reply_text("Количество добавленых записей: {}".format(count))

    elif noRegex.search(user_input):
        update.message.reply_text("Записи не будут добавлены")
    else:
        update.message.reply_text("Некорректная строка. Записи не будут добавлены")

    return ConversationHandler.END


def findEmailCommand(update: Update, context):
    update.message.reply_text("Введите текст для поиска Email: ")
    logging.debug("Запрос на ввод текста с Email")
    return "findEmail"


def findEmail(update: Update, context):
    user_input = update.message.text
    logging.debug("User input: {}".format(user_input))

    emailRegex = re.compile(
        r"[a-zA-Z0-9._%+-]+@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
    )

    emailList = emailRegex.findall(user_input)
    logging.debug("Результат обработки шаблоном: {}".format(emailList))

    if not emailList:
        update.message.reply_text("Email адреса не найдены")
        return  # Завершаем выполнение функции
    context.user_data["email_list"] = emailList

    emails = ""
    for i in range(len(emailList)):
        emails += f"{i+1}. {emailList[i]}\n"

    update.message.reply_text(emails)  #
    logging.debug("результат обработки запроса {}".format(emails))
    update.message.reply_text("Добавить найденные записи в базу данных? (Y/N)")
    return "addEmailDB"


def addEmailDB(update: Update, context):
    count = 0
    user_input = update.message.text
    yesRegex = re.compile(r"^Y$")
    noRegex = re.compile(r"^N$")
    list = context.user_data.get("email_list", "Not found")
    if yesRegex.search(user_input):
        for i in range(len(list)):
            count = count + connectDBAndInsertQuery(
                SQL_QUERIES["insert"].format(
                    table="email_addresses", column="address", value=list[i]
                )
            )
        update.message.reply_text("Количество добавленых записей: {}".format(count))

    elif noRegex.search(user_input):
        update.message.reply_text("Записи не будут добавлены")
    else:
        update.message.reply_text("Некорректная строка. Записи не будут добавлены")
    return ConversationHandler.END


def verifyPasswordCommand(update: Update, context):
    update.message.reply_text("Введите текст для проверки сложности пароля: ")
    logging.debug("Запрос ввода пароля")

    return "verifyPassword"


def verifyPassword(update: Update, context):
    user_input = update.message.text

    passwordComplexityDict = {"simple": "Пароль простой", "strong": "Пароль сложный"}
    score = 0
    passwordStringRegex = re.compile(r"^\S+$")
    charLower = re.compile(r"[a-z]")
    charUpper = re.compile(r"[A-Z]")
    charDigit = re.compile(r"[0-9]")
    charSpecial = re.compile(r"[!@#$%^&*()]")

    passwordString = passwordStringRegex.search(user_input)
    resultVerifyString = passwordComplexityDict["simple"]

    if passwordString:
        if len(user_input) >= 8:
            score += 1
        if charLower.search(user_input):
            score += 1
        if charUpper.search(user_input):
            score += 1
        if charDigit.search(user_input):
            score += 1
        if charSpecial.search(user_input):
            score += 1
    else:
        update.message.reply_text("Некорректная строка для пароля")
        return  # Завершаем выполнение функции

    if score == 5:
        resultVerifyString = passwordComplexityDict["strong"]

    update.message.reply_text(resultVerifyString)  # Отправляем сообщение пользователю
    logging.debug("результат обработки запроса [%s]", len(resultVerifyString))

    return ConversationHandler.END


def getRelease(update: Update, context):
    update.message.reply_text("Информация о релизе")
    result = connectAndExecCommands("get_release")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_release:\n{}".format(result))
    return ConversationHandler.END


def getUname(update: Update, context):
    update.message.reply_text(
        "Информация об архитектуре процессора, имени хоста системы и версии ядра."
    )
    result = connectAndExecCommands("get_uname")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_uname:\n{}".format(result))
    return ConversationHandler.END


def getUptime(update: Update, context):
    update.message.reply_text("Информация о времени работы системы")
    result = connectAndExecCommands("get_uptime")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_uptime:\n{}".format(result))
    return ConversationHandler.END


def getDF(update: Update, context):
    update.message.reply_text("Информация о состоянии файловой системы.")
    result = connectAndExecCommands("get_df")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_df:\n{}".format(result))
    return ConversationHandler.END


def getFree(update: Update, context):
    update.message.reply_text("Информация о состоянии оперативной памяти.")
    result = connectAndExecCommands("get_free")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_free:\n{}".format(result))
    return ConversationHandler.END


def getMpstat(update: Update, context):
    update.message.reply_text("Информация о производительности системы.")
    result = connectAndExecCommands("get_mpstat")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_mpstat:\n{}".format(result))
    return ConversationHandler.END


def getW(update: Update, context):
    update.message.reply_text("Информация о работающих в данной системе пользователях.")
    result = connectAndExecCommands("get_w")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_w:\n{}".format(result))
    return ConversationHandler.END


def getAuths(update: Update, context):
    update.message.reply_text("Последние 10 входов в систему.")
    result = connectAndExecCommands("get_auths")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_auths:\n{}".format(result))
    return ConversationHandler.END


def getCritical(update: Update, context):
    update.message.reply_text("Последние 5 критических события.")
    result = connectAndExecCommands("get_critical")
    update.message.reply_text(result)
    logging.debug("результат обработки запроса get_critical:\n{}".format(result))
    return ConversationHandler.END


def getPS(update: Update, context):
    update.message.reply_text("Информация о запущенных процессах.")
    resultFile(connectAndExecCommands("get_ps"), "resultPS")
    context.bot.send_document(
        update.message.chat.id, document=open("resultPS.txt", "rb")
    )
    logging.debug("результат обработки запроса get_ps в файле resultPS.txt")
    return ConversationHandler.END


def getSS(update: Update, context):
    update.message.reply_text("Информация об используемых портах")
    resultFile(connectAndExecCommands("get_ss"), "resultSS")
    context.bot.send_document(
        update.message.chat.id, document=open("resultSS.txt", "rb")
    )
    logging.debug("результат обработки запроса get_ss в файле resultSS.txt")
    return ConversationHandler.END


def choosedDisplayMode(update: Update, context):
    update.message.reply_text(
        "Введите имя пакета для поиска в системе. Для вывода всех установленных пакетов пришлите ALL"
    )
    return "getAptList"


def getAptList(update: Update, context):
    user_input = update.message.text

    packageStringRegex = re.compile(r"^\S+$")
    allPackageRegex = re.compile(r"^ALL$")

    searchPackage = packageStringRegex.search(user_input)
    if searchPackage:
        if allPackageRegex.search(user_input):
            update.message.reply_text("Вывод всех пакетов")
            resultFile(connectAndExecCommands("get_apt_list"), "resultApt")
        else:
            update.message.reply_text(
                "Результат поиска пакета {}".format(searchPackage[0])
            )
            resultFile(
                connectAndExecCommands("get_dpkg_package", searchPackage[0]),
                "resultApt",
            )
    else:
        update.message.reply_text("Некорректная строка с именем пакета")
        return  # Завершаем выполнение функции

    try:
        context.bot.send_document(
            update.message.chat.id, document=open("resultApt.txt", "rb")
        )
    except FileNotFoundError:
        update.message.reply_text("Запрашиваемый файл resultApt.txt не найден")

    return ConversationHandler.END


def getReplLogs(update: Update, context):
    update.message.reply_text("Вывод логов о репликации")

    #result = subprocess.check_output(COMMANDS["get_repl_logs"], shell=True, text=True, encoding='utf-8')
    resultFile(connectAndExecCommands("get_repl_logs"), "resultRepl")
    context.bot.send_document(
        update.message.chat.id, document=open("resultRepl.txt", "rb")
    )
    context.bot.send_document(
        update.message.chat.id, document=open("resultRepl.txt", "rb")
    )
    logging.debug("результат обработки запроса get_services в файле resultRepl.txt")
    return ConversationHandler.END


def getServices(update: Update, context):
    update.message.reply_text("Информация о запущенных сервисах")
    resultFile(connectAndExecCommands("get_services"), "resultServices")
    context.bot.send_document(
        update.message.chat.id, document=open("resultServices.txt", "rb")
    )
    logging.debug("результат обработки запроса get_services в файле resultServices.txt")
    return ConversationHandler.END

def resultFile(resultCommand, filename):
    resultFile = open("{}.txt".format(filename), "w")
    resultFile.write(resultCommand)
    resultFile.close()


def connectAndExecCommands(command, grep=""):
    #load_dotenv()
    host = os.environ.get("RM_HOST")
    port = os.environ.get("RM_PORT")
    username = os.environ.get("RM_USER")
    password = os.environ.get("RM_PASSWORD")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host, username=username, password=password, port=port)
        logging.debug("Подключение к узлу: {}".format(host))
        stdin, stdout, stderr = client.exec_command(COMMANDS[command].format(grep))
        logging.debug("Выполненеие команды: {}".format(COMMANDS[command].format(grep)))
        data = stdout.read() + stderr.read()

        client.close()
        stdin.close()

        data = str(data).replace("\\n", "\n").replace("\\t", "\t")[2:-1]

    except paramiko.SSHException:
        data = "Ошибка подключения к удаленному узлу"
        logging.debug(
            "Ошибка подключения к удаленному узлу: {}".format(paramiko.SSHException)
        )

    return data


def getEmailsFromDB(update: Update, context):
    update.message.reply_text("Список email-адресов из базы")
    resultList = connectDBAndSelectQuery(
        SQL_QUERIES["select"].format(table="email_addresses")
    )

    emails = ""
    for i in range(len(resultList)):
        emails += f"{resultList[i][0]}. {resultList[i][1]}\n"

    update.message.reply_text(emails)
    logging.debug("результат обработки запроса getEmailsFromDB")
    return ConversationHandler.END


def getPhonesFromDB(update: Update, context):
    update.message.reply_text("Список телефонов из базы")
    resultList = connectDBAndSelectQuery(SQL_QUERIES["select"].format(table="phones"))
    phones = ""
    for i in range(len(resultList)):
        phones += f"{resultList[i][0]}. {resultList[i][1]}\n"

    update.message.reply_text(phones)
    logging.debug("результат обработки запроса getPhonesFromDB")
    return ConversationHandler.END


def connectDBAndSelectQuery(command):
    #load_dotenv()
    dbHost = os.environ.get("DB_HOST")
    dbPort = os.environ.get("DB_PORT")
    dbUsername = os.environ.get("DB_USER")
    dbPassword = os.environ.get("DB_PASSWORD")
    dbName = os.environ.get("DB_DATABASE")
    connection = None

    try:
        connection = psycopg2.connect(
            dbname=dbName,
            user=dbUsername,
            password=dbPassword,
            host=dbHost,
            port=dbPort,
        )
        cursor = connection.cursor()
        cursor.execute(command)
        data = cursor.fetchall()
        logging.info("Команда успешно выполнена")
        return data
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


def connectDBAndInsertQuery(command):
    #load_dotenv()
    dbHost = os.environ.get("DB_HOST")
    dbPort = os.environ.get("DB_PORT")
    dbUsername = os.environ.get("DB_USER")
    dbPassword = os.environ.get("DB_PASSWORD")
    dbName = os.environ.get("DB_DATABASE")
    connection = None
    try:
        connection = psycopg2.connect(
            dbname=dbName,
            user=dbUsername,
            password=dbPassword,
            host=dbHost,
            port=dbPort,
        )
        cursor = connection.cursor()
        cursor.execute(command)
        connection.commit()
        count = cursor.rowcount
        return count
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()


def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    #load_dotenv()
    TOKEN = os.environ.get("TOKEN")
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler("find_Phone_Number", findPhoneNumbersCommand)],
        states={
            "findPhoneNumbers": [
                MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)
            ],
            "addPhoneNumbers": [
                MessageHandler(Filters.text & ~Filters.command, addPhoneNumbers)
            ],
        },
        fallbacks=[],
    )

    convHandlerEmails = ConversationHandler(
        entry_points=[CommandHandler("find_email", findEmailCommand)],
        states={
            "findEmail": [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            "addEmailDB": [MessageHandler(Filters.text & ~Filters.command, addEmailDB)],
        },
        fallbacks=[],
    )

    convHandlerPassword = ConversationHandler(
        entry_points=[CommandHandler("verify_password", verifyPasswordCommand)],
        states={
            "verifyPassword": [
                MessageHandler(Filters.text & ~Filters.command, verifyPassword)
            ],
        },
        fallbacks=[],
    )

    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler("get_apt_list", choosedDisplayMode)],
        states={
            "getAptList": [MessageHandler(Filters.text & ~Filters.command, getAptList)]
        },
        fallbacks=[],
    )

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("get_release", getRelease))
    dp.add_handler(CommandHandler("get_uname", getUname))
    dp.add_handler(CommandHandler("get_uptime", getUptime))
    dp.add_handler(CommandHandler("get_df", getDF))
    dp.add_handler(CommandHandler("get_free", getFree))
    dp.add_handler(CommandHandler("get_mpstat", getMpstat))
    dp.add_handler(CommandHandler("get_w", getW))
    dp.add_handler(CommandHandler("get_auths", getAuths))
    dp.add_handler(CommandHandler("get_critical", getCritical))
    dp.add_handler(CommandHandler("get_ss", getSS))
    dp.add_handler(CommandHandler("get_ps", getPS))
    dp.add_handler(CommandHandler("get_services", getServices))
    dp.add_handler(CommandHandler("get_emails", getEmailsFromDB))
    dp.add_handler(CommandHandler("get_phone_numbers", getPhonesFromDB))
    dp.add_handler(CommandHandler("get_repl_logs", getReplLogs))

    dp.add_handler(convHandlerAptList)
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerEmails)
    dp.add_handler(convHandlerPassword)

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == "__main__":
    main()
