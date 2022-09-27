import TT_utils

dirpath = TT_utils.dirpath

session_len_add_to_encrypt = 13

url_login = "https://"
url_data = "https://"

def login(data, url_login=url_login, url_data=url_data):
    sessionfile=dirpath+"session.txt"
    old_session_data=None
    cookie_data={}
    login_data = {
        "form_id":"user_login_form",
    }
    login_data["name"] = data[0]
    login_data["pass"] = data[1]                            

    try:
        session_fh=open(sessionfile,"r", encoding="utf-8-sig")
        old_session_data=session_fh.read()
        old_session_data = TT_utils.decrypt(old_session_data, len(old_session_data)+session_len_add_to_encrypt)
        session_fh.close()
    except:
        print("Сохраненная сессия отсутствует, входим по паролю")

    if old_session_data != None:
        tempcookie=old_session_data.split()
        datacount=0
        for i in tempcookie:
            if len(i)>36:
                if i.startswith("SPL"):
                    try:
                        cookie_data[i.split("=")[0]]=i.split("=")[1] #cookie_data[SPL041c12df7672e9faf30442464cc13d7e]=<SPL041c12df7672e9faf30442464cc13d7e_data>
                    except:
                        continue
                    datacount+=1
                if i.startswith("SSESS"):
                    try:
                        cookie_data[i.split("=")[0]]=i.split("=")[1]
                    except:
                        continue
                    datacount+=1
        if datacount == 2:
            isOldSession=True
        else:
            print("Сессия отсутствует или повреждена, входим по паролю")
            isOldSession=False
    else:
        isOldSession=False

    isLoggedIn=False
    if isOldSession:
        print("Входим с использованием сохранённой сессии...")
        try:
            page = TT_utils.loadpage(url=url_data, method="get", cookie_data=cookie_data)
        except:
            page = False
        if page.status_code == 200:
            isLoggedIn=True
        elif page.status_code == 403:
            print("Сессия недействительна, входим по паролю")
        else:
            print("Ошибка доступа к данным о термических точках")

    if not isLoggedIn:
        page = TT_utils.loadpage(url=url_login, method="post", data=login_data)
        if page.content.decode().startswith("Учётная запись временно"):
            print("Учётная запись временно заблокирована по причине более 5 неудачных попыток входа.")
            print("Попробуйте войти позже или используйте другие учётные данные для входа.\n")
            return
        page = TT_utils.loadpage(url=url_data, method="get", cookie_data=page.cookies)
        #если пароль неверный, то будет возвращён json с единственным полем message,
        #в котором будет написано
        #"The 'restful get thermal_point' permission is required."
        if page.status_code == 200:
            isLoggedIn=True
            new_sess = str(page.cookies)
            new_sess = TT_utils.encrypt(new_sess,len(new_sess)+session_len_add_to_encrypt)
            with open(sessionfile, "wt") as sessfh:
                sessfh.write(new_sess)
        elif page.status_code == 403:
            print("Неверные имя пользователя или пароль")
        else:
            print("Произошла ошибка входа, попробуйте позже")

    if isLoggedIn:
        print("Вход успешен")
        if isOldSession:
            return(cookie_data)
        return(page.cookies)

if __name__ == "__main__":
    print("Логин:")
    name = input()
    print("Пароль:")
    pwd = input()                        
    login([name,pwd])
