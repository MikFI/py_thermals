import os
import sys
import time
import uuid
import random
import requests
import subprocess

#длина шифрованного текста
message_len = 40
session=requests.session()

def get_path():
    #определяем, является ли наш скрипт скомпилированным в exe (pyinstaller --onefile) 
    if getattr(sys, "frozen", False):
        dirpath = os.path.dirname(sys.executable) + "\\"
    #или нет (`.py` / `.pyw`)
    elif __file__:
        dirpath = os.path.dirname(__file__) + "\\"
    return dirpath

def get_config():    
    config = {}
    try:
        with open(dirpath+"config.txt", "rt", encoding="UTF-8-sig") as fhr:
            lines = fhr.read().split("\n")
        for i in lines:
            if i == "": continue
            if i.startswith("//"): continue
            else: 
                tmp = i.split("=")
                config[tmp[0]] = tmp[1]
    except:
        print("Конфигурационный файл отсутствует, требуется ввод логина-пароля\nВведите логин и нажмите Enter:")
        login = encrypt(input().strip())
        print("Введите пароль и нажмите Enter:")
        password = encrypt(input().strip())
        # print("Введите код своего субъекта (по ГИБДД) и нажмите Enter:")
        # region = input()
        checkrate = 1
        sound = "Alarm01.wav"
        test = 0
        # continuous = 1
        txt = "//имя(email) и пароль пользователя для входа в систему\n"
        txt += f"login={login}\npassword={password}\n\n"
        # txt += "//код субъекта РФ (основной номер по классификации ГИБДД)\n"
        # txt += f"region={region}\n\n"
        txt += "//звук для оповещения (только в формате wav)\n"
        txt += f"sound={sound}\n\n"
        txt += "//частота опроса сайта (в минутах)\n"
        txt += f"checkrate={checkrate}\n\n"
        txt += "//тестовый режим (показывает все термоточки за последний год, а не только новые)\n"
        txt += "//0 (нет) или 1 (да)\n"
        txt += f"test={test}\n\n"
        # txt += "//параметр для установки скрипта в режим постоянной работы (1)\n"
        # txt += "//или для одноразовой проверки - чтобы, к примеру, установить его в планировщик задач (0)\n"
        # txt += f"continuous={continuous}\n\n"
        with open(dirpath+"config.txt", "wt", encoding="UTF-8") as fhw:
            fhw.write(txt)
        print("При желании вы всегда можете изменить введенные данные в файле config.txt")
        config["login"] = login
        config["password"] = password
        # config["region"] = region
        config["checkrate"] = checkrate
        config["sound"] = sound
        config["test"] = test
        # config["continuous"] = continuous
    if int(config["checkrate"]) < 1: config["checkrate"] = "1"
    return config

#блок для одноразового исполнения скрипта (для планировщика)
#проверяет данные в файле last.txt
def get_latest_check():
    latest = {}
    try:
        with open(dirpath+"last.txt", "rt", encoding="UTF-8-sig") as fhr:
           lines = fhr.read().split("\n")
        for i in lines:
            if i == "": continue
            if i.startswith("//"): continue
            else: 
                tmp = i.split("=")
                latest[tmp[0]] = tmp[1]
    except:
        latest["last_date"] = "2020-01-01 00:00:00"
        latest["last_timestamp"] = "0"
        latest["last_num"] = "0"
        #уровень предупреждений при инициализации сразу ставим 1 - новые ТТ
        #его сбросят в 0, а при первичном запуске скрипта нам не нужно, 
        #чтобы выскакивало уведомление про "0 новых термоточек"
        latest["f_warn"] = "1"
        latest["upd_check"] = "0"
        txt = "\n".join([key + "=" + value for key,value in latest.items()])
        with open(dirpath+"last.txt", "wt", encoding="UTF-8") as fhw:
            fhw.write(txt)
    return latest

def renew_login_data(config):
    print("Введите корректные логин и пароль\nВведите логин и нажмите Enter:")
    login = encrypt(input().strip())
    config["login"] = login
    print("Введите пароль и нажмите Enter:")
    password = encrypt(input().strip())
    config["password"] = password

    with open(dirpath+"config.txt", "rt", encoding="UTF-8-sig") as fhr:
        lines = fhr.read().split("\n")
    i = 0
    while i < len(lines):
        if lines[i] == "" or lines[i].startswith("//"):
            i += 1
            continue
        else: 
            tmp = lines[i].split("=")
            if tmp[0] == "login": tmp[1] = login
            if tmp[0] == "password": tmp[1] = password
            lines[i] = "=".join(tmp)
            i += 1
    txt = "\n".join(lines)
    with open(dirpath+"config.txt", "wt", encoding="UTF-8") as fhw:
        fhw.write(txt)
    return config

def renew_latest_check(latest):
    txt = "\n".join([key + "=" + value for key,value in latest.items()])
    with open(dirpath+"last.txt", "wt", encoding="UTF-8") as fhw:
        fhw.write(txt)

def loadpage(url,cookie_data=None,method="get",data=None,urladd=None,urljson=None):
    if method == "get": method = session.get
    else: method = session.post
    while True:
        try:
            page = method(
                url=url,
                cookies=cookie_data,
                data=data,
                params=urladd,
                json=urljson
            )
            page.cookies = session.cookies
            if (page.status_code == 200):
                break
            if (page.status_code == 400):
                print ("400-НЕКОРРЕКТНЫЙ ЗАПРОС")
                time.sleep(1)
                break
            if (page.status_code == 403):
                print ("403-ДОСТУП ЗАПРЕЩЕН")
                time.sleep(1)
                break
            if (page.status_code == 404):
                print ("404-СТРАНИЦА НЕ НАЙДЕНА")
                time.sleep(1)
                break
            if (page.status_code == 405):
                print ("405-МЕТОД НЕ ПОДДЕРЖИВАЕТСЯ")
                time.sleep(1)
                break
            if (page.status_code == 406):
                print ("406-НЕПРИЕМЛЕМО")
                time.sleep(1)
                break
            if (page.status_code == 500):
                print ("500-ВНУТРЕННЯЯ ОШИБКА СЕРВЕРА")
                countdown(30)
            if (page.status_code == 502):
                print ("502-ОШИБКА ШЛЮЗА")
                countdown(30)
        except:
            print("Ошибка получения данных")
            countdown(30)
    return page

def countdown(count):
    n = count
    while n>0:
        print(f"Повторная попытка через {str(n).zfill(2)}", end="\r")
        n -= 1
        time.sleep(1)

#довольно фиговый алгоритм шифрования, но я не криптограф, увы
def encrypt(text, message_len=message_len):
    symbols = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    if len(text) < message_len: text += chr(128)
    while len(text) < message_len:
        text += random.choice(symbols)
    list_text = [ord(x) for x in text]
    list_key = get_key(message_len)
    pos = 0
    while pos < len(list_text):
        list_text[pos] = (list_text[pos] + list_key[pos]).to_bytes(2,"big")[1]
        pos+=1
    return "".join([f"{x:0>2X}" for x in list_text])

def decrypt(text, message_len=message_len):
    list_text = " ".join(text[x:x+2] for x in range(0, len(text),2)).split() 
    list_text = [int(x, 16) for x in list_text]
    list_key = get_key(message_len)
    pos = 0
    last_symbol = 0
    while pos < len(list_text):
        if list_text[pos] <= list_key[pos] : list_text[pos] += 256
        list_text[pos] = (list_text[pos] - list_key[pos]).to_bytes(2,"big")[1]
        if list_text[pos] == 128:
            last_symbol = pos
            break
        pos+=1
    return "".join([chr(x) for x in list_text[:last_symbol]])
    
def get_key(message_len=message_len):
    key1 = ""
    key2 = ""
    #блокируем появление окна
    #(появляется при вызове серийника)
    #работает только для винды
    startupinfo = None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    serials = subprocess.check_output("wmic diskdrive get Name, SerialNumber",startupinfo=startupinfo).decode().split("\n")
    for i in serials:
        if "DRIVE0" in i:
            key1 = i.split("DRIVE0")[-1].strip()
    key2 = uuid.uuid1().urn.split("-")[-1]
    sum_key = key1+key2
    key_main = key1+key2
    while len(key_main) < message_len:
        key_main += sum_key
    list_key = [ord(x) for x in key_main[:message_len]]
    list_add = [ord(x) for x in key_main[message_len:]]
    pos = 0
    while pos < len(list_add):
        list_key[pos] = (list_key[pos] + list_add[pos]).to_bytes(2,"big")[1]
        pos+=1
    return list_key

dirpath = get_path()
config = get_config()
