import winsound
from tkinter import *
from tkinter import ttk
import TT_updater
import webbrowser
import TT_utils

dirpath = TT_utils.dirpath
config = TT_utils.config
sound = config["sound"]

def close_window(window):
    window.destroy()
    winsound.PlaySound(None, winsound.SND_ASYNC)
   
def center(window):
    #window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    size = tuple(int(n) for n in window.geometry().split("+")[0].split("x"))
    x = screen_width/2 - size[0]/2
    y = screen_height/2 - size[1]/2

    window.geometry("+%d+%d" % (x, y))

def download_update(url,win):
    close_window(win)
    try:
        print("Скачиваем обновление...")
        TT_updater.download_new(url)
    except:
        print("Не могу скачать, попробуйте вручную, по ссылке:")
        print(url+"\n")
        webbrowser.open(url)

def base_dialogue():
    root = Tk()
    root.title("ВНИМАНИЕ!")
    root.geometry("260x100+0+0")
    root.resizable(False, False)
    root.attributes("-toolwindow", True)
    root.attributes("-topmost",True)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    ttk.Style().configure("my.TButton", font=("Helvetica", 12))
    ttk.Frame(root, padding="3 3 12 12")\
        .grid(column=2, row=2)
    root.protocol("WM_DELETE_WINDOW", lambda tw=root:close_window(tw))
    root.bind("<Escape>", lambda event: close_window(root))
    center(root)
    root.focus_force()
    return root

def dialogue_newTT(label="НОВЫЕ ТЕРМОТОЧКИ"):
    window = base_dialogue()
    winsound.PlaySound(dirpath+sound, winsound.SND_ASYNC|winsound.SND_LOOP)
    ttk.Label(window, text=label, font=("Courier", 12))\
        .grid(column=0, row=0)
    ttk.Button(window, text="Принято", style="my.TButton",command=lambda tw=window:close_window(tw))\
        .grid(column=0, row=1)
    window.bind("<Return>", lambda event=window:close_window(window))
    for child in window.winfo_children(): 
        child.grid_configure(padx=5, pady=5)
    window.mainloop()

def dialogue_update(update_url):
    window = base_dialogue()
    winsound.PlaySound(dirpath+sound, winsound.SND_ASYNC)
    ttk.Label(window, text="Доступно обновление", font=("Courier", 12))\
        .grid(column=0, row=0, columnspan=2)
    ttk.Button(window, text="Скачать", style="my.TButton",command=lambda: download_update(update_url, window))\
        .grid(column=0, row=1, sticky=E)
    ttk.Button(window, text="Пропустить", style="my.TButton",command=lambda tw=window:close_window(tw))\
        .grid(column=1, row=1, sticky=W)
    window.bind("<Return>", lambda event: download_update(update_url, window))
    for child in window.winfo_children(): 
        child.grid_configure(padx=5, pady=5)
    window.mainloop() 
