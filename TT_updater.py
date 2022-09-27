import os
import sys
import time
import requests
import subprocess
from tqdm import tqdm

import TT_utils

dirpath = TT_utils.dirpath

#проверка обновлений
def check_update(current_ver):
    clean_bak_files()
    try:
        #сюда надо будет вставить ссылку на текстовик, содержащий инфу о наличии обновления
        #внутри текстовика всего две строки
        #1 - номер актуальной версии
        #2 - ссылка на exe-файл новой версии
        update_url = ''

        page = requests.get(update_url)
        if (page.status_code == 200):
            data = page.content.decode("UTF-8").split('\n')
            if current_ver < float(data[0]):
                return data[1]
            else: return ""
    except:
        return ""

#проверяем update.txt и, по необходимости (прошло более 10 дней)
#чистим его и файлы бэкапа
def clean_bak_files():
    if (os.path.isfile(dirpath + "update.txt")):
        towrite = ""
        with open(dirpath+"update.txt", "r", encoding="UTF-8") as fhr:
            lines = fhr.read().split("\n")
        for i in lines:
            item = i.split("=")
            if len(item) != 2:
                continue
            if (time.time() - int(item[0]) > 864000):
                try:
                    os.remove(item[1])
                except:
                    pass
            else:
                towrite += i + "\n"
        if towrite == "":
            os.remove(dirpath+"update.txt")
        else:
            with open(dirpath+"update.txt", "wt", encoding="UTF-8") as fhw:
                fhw.write(towrite)

#скачиваем новое обновление
def download_new(url):
    df = requests.get(url, stream=True)
    fsize = int(df.headers.get('content-length', 0))
    fname = df.headers['content-disposition'].split('=')[1].strip('"')
    
    fname = get_newfilename(fname)
    #поскольку качаем экзешку, меняем ей расширение на ex_, потому что хз, 
    #какие на компе политики по скачиванию бинарников из интернетов
    if fname.endswith('exe'):
        fname = fname[:-1]+'_'

    with open(dirpath + fname, 'wb') as file, tqdm(
        desc=fname,
        total=fsize,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in df.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)
    #переименовываем обратно уже после скачивания
    #файл к этому моменту должен быть уже точно сохранён
    #иначе данная функция просто упадёт
    try:
        os.rename(dirpath + fname, dirpath + fname[:-1]+'e')
        fname = fname[:-1]+'e'
        #ждём, не заблочит ли винда или антивирь по какому-то своему поводу
        #в теории, не должны, но мало ли...
        time.sleep(2)
        #если не заблочили, значит всё ок
        if (os.path.isfile(dirpath + fname)):
            print("Обновление успешно сохранено по адресу:")
            print(dirpath + fname + "\n")
            update_app(fname)
        else:
            print(f"Операционная система не принимает {fname}")
            print("Проверьте политики безопасности и антивирусное ПО")
        
    except:
        print(f"Не удалось переименовать {fname}")
        print(f"Проверьте {dirpath + fname} и замените файл в ручном режиме")
        print(f"(требуется заменить {os.path.basename(sys.executable)} на {fname})")
    
def update_app(updname):
    print("Обновляем...")
    appname = os.path.basename(sys.executable)
    backup_fname = get_newfilename(appname + '.BAK')
    os.rename(dirpath + appname, dirpath + backup_fname)
    os.rename(dirpath + updname, dirpath + appname)

    #создаём (или дописываем) файл update.txt, в котором
    #сохраняем инфу о дате обновления и названии файла бэкапа
    mode = "wt"
    if (os.path.isfile(dirpath + 'update.txt')):
        mode = 'a'
    text = f"{int(time.time())}={backup_fname}\n"
    with open(dirpath+'update.txt', mode, encoding="UTF-8") as fhw:
        fhw.write(text)

    subprocess.run(dirpath + appname)
    sys.exit()

def get_newfilename(fname):
    file_list = [f for f in os.listdir(dirpath) if os.path.isfile(dirpath+f)]
    if fname in file_list:
        n = 1
        fext = fname[-3:]
        fname = fname[:-4]
        while True:
            if fname+f" ({n})."+fext in file_list: n+=1
            else: return fname+f" ({n})."+fext
    return fname
