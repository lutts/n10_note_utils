import os
from tkinter import *
from tkinter.ttk import *
import tkinter.font as tkFont

from keyboard_monitor import start_keyboard_hook
from keyboard_monitor import clipboard_markdown_to_html, n10notes_process
from keyboard_monitor import send_markdown_to_onenote, list_markdown_latex_equations
from keyboard_monitor import send_markdown_to_supermemo, generate_supermemo_qa
from keyboard_monitor import start_note_monitor, run_supermemo

# writing code needs to
# create the main window of
# the application creating
# main window object named root
root = Tk()

icon_path = os.path.dirname(__file__)
icon_path = os.path.dirname(icon_path)
icon_path = os.path.join(icon_path, "data", "notes.ico")
root.iconbitmap(icon_path)
# giving title to the main window
root.title("First_Program")

fontObj = tkFont.Font(family="Microsoft Yahei", size=16)
style = Style()
#style.theme_use('winnative')
style.configure('TButton', font=fontObj)

#root.geometry('500x500') 

btn = Button(root, text='整理读书笔记(Capslock + p)',
             command=n10notes_process)
btn.grid(row=0, column=0, sticky='ew', pady=2)

btn = Button(root, text='转换markdown为onenote格式(Capslock + o)',
             command=send_markdown_to_onenote)
btn.grid(row=2, column=0, sticky='ew', pady=2)

btn = Button(root, text='列出markdown中的LaTex公式(Capslock + l)',
             command=list_markdown_latex_equations)
btn.grid(row=3, column=0, sticky='ew', pady=2)

btn = Button(root, text='转换markdown为supermemo html格式(Capslock + u)',
             command=send_markdown_to_supermemo)
btn.grid(row=4, column=0, sticky='ew', pady=2)

btn = Button(root, text='转换markdown为supermemo Q&A格式(Capslock + q)',
             command=generate_supermemo_qa)
btn.grid(row=5, column=0, sticky='ew', pady=2)

btn = Button(root, text='启动笔记摘抄程序notes monitor(Capslock + n)',
             command=start_note_monitor)
btn.grid(row=6, column=0, sticky='ew', pady=2)

btn = Button(root, text='启动supermemo(Capslock + s)',
             command=run_supermemo)
btn.grid(row=7, column=0, sticky='ew', pady=2)

btn = Button(root, text='转换剪贴板中的markdown为html格式(Capslock + m)',
             command=clipboard_markdown_to_html)
btn.grid(row=8, column=0, sticky='ew', pady=2)

lbl = Label(root, text="其他快捷键: ")
lbl.grid(row=9, column=0, sticky='w', pady=2)

lbl = Label(root, text="Capslock + c: 类似于Ctrl+c，但拷贝的结果永远是纯文本")
lbl.grid(row=10, column=0, sticky='w', pady=2)

lbl = Label(root, text="Capslock + d: Ctrl+c，然后查询GoldenDict词典，需要将GoldenDict的hotkey设置为Ctrl+Alt+Shift+C")
lbl.grid(row=11, column=0, sticky='w', pady=2)

lbl = Label(root, text="Capslock + v: 类似于Ctrl+v，但会对文本进行基于markdown的规范化")
lbl.grid(row=12, column=0, sticky='w', pady=2)

lbl = Label(root, text="Capslock + b: 类似于Ctrl+v，但会将粘贴的文本转换为theBrain的markdown格式")
lbl.grid(row=13, column=0, sticky='w', pady=2)

lbl = Label(root, text="Capslock + t: 即ctrl+shift+f12，用于将supermemo的html component转换为text component")
lbl.grid(row=14, column=0, sticky='w', pady=2)


lbl = Label(root, text="Capslock + 1: 和notes_monitor配合，将拷贝的内容转换成markdown level 1 header")
lbl.grid(row=15, column=0, sticky='w', pady=2)
lbl = Label(root, text="Capslock + 2: 和notes_monitor配合，将拷贝的内容转换成markdown level 2 header")
lbl.grid(row=16, column=0, sticky='w', pady=2)
lbl = Label(root, text="Capslock + 3: 和notes_monitor配合，将拷贝的内容转换成markdown level 3 header")
lbl.grid(row=17, column=0, sticky='w', pady=2)
lbl = Label(root, text="Capslock + 4: 和notes_monitor配合，将拷贝的内容转换成markdown level 4 header")
lbl.grid(row=18, column=0, sticky='w', pady=2)
lbl = Label(root, text="Capslock + 5: 和notes_monitor配合，将拷贝的内容转换成markdown level 5 header")
lbl.grid(row=19, column=0, sticky='w', pady=2)
lbl = Label(root, text="Capslock + 6: 和notes_monitor配合，将拷贝的内容转换成markdown level 6 header")
lbl.grid(row=20, column=0, sticky='w', pady=2)

# calling mainloop method which is used
# when your application is ready to run
# and it tells the code to keep displaying
start_keyboard_hook()
root.mainloop()
