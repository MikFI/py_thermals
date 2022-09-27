import json
import time
import datetime

import TT_utils
import TT_login
import TT_updater
import TT_GUI

dirpath = TT_utils.dirpath

#отсюда мы получаем все данные
url = "https://"

#текущая версия
ver = 0.3

#этой опцией контролируется, будет ли скрипт работать постоянно
#(должно быть расширение py, чтобы висело окно)
#или же нужно забить его в планировщик (расширение pyw)
continuous = 1

#временный костыль, чтобы сообщение о новых ТТ не насиловало мозг при каждой проверке
#(раз в минуту может быть слишком маленьким интервалом, чтобы среагировать)
#поэтому сообщение будет задерживаться на n минут, выводясь при ближайшей проверке
#по истечении этого интервала
delay = 5
elapsed = delay

config = TT_utils.config
login = TT_utils.decrypt(config["login"])
password = TT_utils.decrypt(config["password"])
# region = config["region"]
sound = config["sound"]
checkrate = int(config["checkrate"])
#уведомлять только о новых термоточках, или вообще о всех подряд (тестовый режим)
notify_all = int(config["test"])
# continuous = int(config["continuous"])

if "ver" in config:
    ver = float(config["ver"])

#выставляем диапазон дат для проверки
def get_daterange(delta=7):
    now = datetime.datetime.now()
    diff = datetime.timedelta(days=delta)
    end = now
    end = end + datetime.timedelta(days=1)
    start = end-diff
    str_start =  str(start.day).zfill(2)+"."+str(start.month).zfill(2)+"."+str(start.year)
    str_end = str(end.day).zfill(2)+"."+str(end.month).zfill(2)+"."+str(end.year)
    return str_start + " - " + str_end

#формируем список полей, добавляемых к ссылке
def get_payload(days):
    daterange = get_daterange(days)
    payload = {
        "_format":"json",
        "filters[1][field]":"date_report",
        "filters[1][value]":daterange,
        "filters[1][type]":"date_range",
        # "filters[2][field]":"subject.id",
        # "filters[2][value]":region,
        "_renderer":"tabulator",
        "page":"1",
        "size":"100"
    }
    return payload

#проверка на один раз (если частота работы скрипта будет контролироваться извне)
def single_check():
    latest = TT_utils.get_latest_check()
    last_upd = int(latest["upd_check"])
    now = time.time()
    #проверяем обновления раз в сутки для проверки по расписанию
    if (now - last_upd)>86400:
        new_version = TT_updater.check_update(ver)
        if new_version != "":
            TT_GUI.dialogue_update(update_url=new_version)
        latest["upd_check"] = str(int(now))
        TT_utils.renew_latest_check(latest)

    #уведомляшка на все подряд ТТ (тестовый режим работы)
    if notify_all:
        payload = get_payload(days=365)
        page = TT_utils.loadpage(url,method="get",cookie_data=cookie_data,urladd=payload)
        if page.status_code == 200:
            page = json.loads(page.content.decode("utf-8"))
            total = int(page["total"])
            TT_GUI.dialogue_newTT("НОВЫХ ТЕРМОТОЧЕК:"+str(total))
        return

    #стандартный режим работы
    payload = get_payload(days=2)
    data = []
    num_page = 1
    while True:
        page = TT_utils.loadpage(url,cookie_data=cookie_data,method="get",urladd=payload)
        if page.status_code == 200:
            page = json.loads(page.content.decode("utf-8"))
            data += page["data"]
            if page["last_page"] > num_page:
                num_page += 1
                payload["page"] = str(num_page)
            else:
                total = int(page["total"])
                break
        else: break

    new_tt = 0
    last_TT_timestamp = int(latest["last_timestamp"])
    f_warn = int(latest["f_warn"])
    last_tt = None
    if total > 0:
        for tt in data:
            tt_date = tt["created"]
            tt_date_timestamp = datetime.datetime.strptime(tt_date,"%Y-%m-%d %H:%M:%S")
            tt_date_timestamp = int(time.mktime(tt_date_timestamp.timetuple()))
            if tt_date_timestamp>last_TT_timestamp:
                new_tt += 1
                last_tt = tt
        if new_tt>0:
            latest["last_date"] = last_tt["created"]
            latest["last_timestamp"] = str(tt_date_timestamp)
            latest["last_num"] = str(last_tt["number"])
            f_warn = 0
            latest["f_warn"] = "1" 
            TT_utils.renew_latest_check(latest)

    #число напоминалок (если ТТ не взята в работу) - три раза
    if f_warn<3:
        if f_warn == 0:
            TT_GUI.dialogue_newTT("НОВЫХ ТЕРМОТОЧЕК:"+str(new_tt))
            f_warn += 1
            return
        f_warn += 1
        payload["filters[0][field]"]="status"
        payload["filters[0][value]"]="new"
        page = TT_utils.loadpage(url,cookie_data=cookie_data,method="get",urladd=payload)
        data = json.loads(page.content.decode("utf-8"))
        if int(data["total"]) > 0:
            latest["f_warn"] = str(f_warn)
            TT_utils.renew_latest_check(latest)
            TT_GUI.dialogue_newTT("ТЕРМОТОЧЕК НЕ ВЗЯТО В РАБОТУ:"+data["total"])

def loop_check():
    global elapsed
    while True:
        elapsed += checkrate
        payload = get_payload(days=365)
        #если НЕ выставлен флаг "тестового режима", оповещаем только о новых
        #термоточках, в противном случае, ловим всё подряд
        if notify_all != 1: 
            payload["filters[0][field]"]="status"
            payload["filters[0][value]"]="new"
   
        now = datetime.datetime.now()
        print("Проверка новых ТТ:", now.strftime("%d.%m.%Y, %H:%M"))
        page = TT_utils.loadpage(url,cookie_data=cookie_data,method="get",urladd=payload)
        if page.status_code == 200:
            page = json.loads(page.content.decode("utf-8"))
            if int(page["total"]) > 0:
                print("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                print(f"Обнаружено термических точек: {page['total']}")
                limit = 5
                for i in range(min(limit,int(page["total"]))):
                    print_TT(page["data"][i])
                if int(page["total"]) > limit:
                    print("...")
                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n")
                if elapsed >= delay:
                    TT_GUI.dialogue_newTT("НОВЫХ ТЕРМОТОЧЕК:"+str(page["total"]))
            else:
                True
        time.sleep(checkrate*60)
        if elapsed >= delay: elapsed = 0

def print_TT(TT):
    distance = TT["settlement_distance"]+"м"
    num = TT["number"]
    settlement = TT["settlement_name"]
    if TT["is_test"] == "1":
        istest = "(учебная)"
    else:
        istest = ""
    print(f"{istest} №{num}, {distance} от н.п. {settlement}")

#пытаемся залогиниться, пока не посинеем (или пока программу не закроют)
while True:
    cookie_data = TT_login.login([login,password])
    if cookie_data == None:
        config = TT_utils.renew_login_data(config)
        login = TT_utils.decrypt(config["login"])
        password = TT_utils.decrypt(config["password"])
    else:
        break

print(f"Версия программы {ver}")
if not continuous:
    single_check()
else:
    #проверяем обновления перед каждым запуском "бесконечной" версии
    new_version = TT_updater.check_update(ver)
    if new_version != "":
        TT_GUI.dialogue_update(update_url=new_version)
    loop_check()
