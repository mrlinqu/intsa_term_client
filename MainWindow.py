# Copyright 2020 by Roman Khuramshin <mr.linqu@gmail.com>.
# All rights reserved.
# This file is part of the Intsa Term Client - X2Go terminal client for Windows,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.


from tkinter import *
from tkinter.ttk import *
from tkinter import font
from tkinter import filedialog
import threading
import config
import logging

import win32print

all_printers = [printer[2] for printer in win32print.EnumPrinters(2)]
PRN_NOT_USE = 'Не использовать'
all_printers.insert(0, PRN_NOT_USE)


class MainWindow(threading.Thread):
    toplevel_dialog = None
    # def __init__(self):
    #     super().__init__()
    #     pass

    def run(self):
        logging.debug('main window thread id: %s',threading.get_ident())
        self.root = Tk()

        self.root.title("Insta : Подключение к удаленному рабочему столу")
        
        wnd_w = 350
        wnd_h = 270
        wnd_x = int(self.root.winfo_screenwidth()/2 - wnd_w/2)
        wnd_y = int(self.root.winfo_screenheight()/2 - wnd_h/2)
        self.root.geometry('%sx%s+%s+%s' % (wnd_w, wnd_h, wnd_x, wnd_y))

        #self.root.geometry("350x270+300+300")
        #self.root.geometry("430x460+300+300")

        self.root.resizable(False, False)

        self.root.bind("<Escape>", self.on_keyEsc)
        self.root.bind("<Return>", self.on_keyReturn)
        self.root.protocol("WM_DELETE_WINDOW", self.on_wnd_delete)


        self.username = StringVar()
        self.username.set(config.get('username',''))
        self.passwd = StringVar()
        self.statusText = StringVar()
        #self.statusText.set('Lorem ipsum dolor sit amet, consectetur adipiscing elit')
        self.statusText.set('Подключение...')
        self.paramsShowed = False


        self.initWnd(self.root)

        self.root.mainloop()

    def setStatus(self, text):
        self.statusText.set(text)
        pass

    def lock(self):
        self.setState('disabled')
        pass

    def unlock(self):
        self.setState('normal')
        pass

    def setState(self, state):
        #self.input_login.config(state=state)
        #self.input_password.config(state=state)
        #self.btnOk.config(state=state)
        pass

    def close(self):
        self.root.quit()
        pass
    
    
    ################################################################################################
    ################################################################################################


    def showStatusModal(self):
        self.root.wm_attributes("-disabled", True)

        # Creating the toplevel dialog
        self.toplevel_dialog = Toplevel(self.root)

        x = self.root.winfo_x() + (15 if self.paramsShowed else -25)
        y = self.root.winfo_y() + 130

        #self.toplevel_dialog.minsize(300, 100)
        #self.toplevel_dialog.geometry("400x110+300+300")
        
        #self.toplevel_dialog.wm_attributes('-fullscreen','true')
        self.toplevel_dialog.wm_attributes('-toolwindow','true')

        self.toplevel_dialog.geometry("400x110+%s+%s" % (x, y,))
        self.toplevel_dialog.resizable(False, False)
        
        self.toplevel_dialog.title("Подключение...")

        # Tell the window manager, this is the child widget. Interesting, if you want to let the child window flash if user clicks onto parent
        self.toplevel_dialog.transient(self.root)

        # This is watching the window manager close button and uses the same callback function as the other buttons (you can use which ever you want, BUT REMEMBER TO ENABLE THE PARENT WINDOW AGAIN)
        self.toplevel_dialog.protocol("WM_DELETE_WINDOW", self.on_statusModal_btnClancel_click)

        Frame(self.toplevel_dialog, ).pack(fill=X, pady=10,)

        label = Label(self.toplevel_dialog, textvariable=self.statusText)
        label.pack(fill=X, expand=True, padx=20,)

        Frame(self.toplevel_dialog, ).pack(fill=X, pady=10,)
        
        Frame(self.toplevel_dialog, ).pack(side=BOTTOM, fill=X, pady=10,)
        
        btn = Button(self.toplevel_dialog, text='Отмена', width=12, command=self.on_statusModal_btnClancel_click)
        btn.pack(side='right', padx=20,)

        pass

    def closeStatusModal(self):
        self.root.wm_attributes("-disabled", False) # IMPORTANT!
        self.toplevel_dialog.destroy()
        self.toplevel_dialog = None

        self.root.deiconify()
        pass

    def initWnd(self, parent):
        #########################################################################
        logoFrame = Frame(parent, )#borderwidth=2, relief='groove')
        logoFrame.pack(side=TOP, fill=X, padx=30, pady=30,)

        label_logo1 = Label(logoFrame, text="Подключение к удаленному\nрабочему столу", justify='left', font='arial 14', )
        label_logo1.pack(side=LEFT,)

        #########################################################################
        siginFrame = Frame(parent, )#borderwidth=2, relief='groove')
        siginFrame.pack(fill=X, padx=30, pady=0,)

        # username ----------------------------------------------------------------
        usernameFrame = Frame(siginFrame)
        usernameFrame.pack(fill=X, pady=7,)

        usernameLabel = Label(usernameFrame, text="Пользователь:", width=15, )
        usernameLabel.pack(side=LEFT)

        usernameInput = Entry(usernameFrame, textvariable=self.username)
        usernameInput.pack(fill=X, expand=True)

        # passwd ----------------------------------------------------------------
        passwdFrame = Frame(siginFrame)
        passwdFrame.pack(fill=X, pady=7,)

        passwdLabel = Label(passwdFrame, text="Пароль:", width=15, )
        passwdLabel.pack(side=LEFT)           

        passwdInput = Entry(passwdFrame, textvariable=self.passwd, show="●")
        passwdInput.pack(fill=X, expand=True)

        # ----------------------------------------------------------------
        if not self.username.get():
            usernameInput.focus_set()
        else:
            passwdInput.focus_set()
        
        #########################################################################
        btnFrame = Frame(parent, )#borderwidth=2, relief='groove')
        btnFrame.pack(side=BOTTOM, fill=BOTH, padx=30, pady=30,)

        link1 = Label(btnFrame, text="Параметры", cursor="hand2")
        link1.pack(side=LEFT)
        f = font.Font(link1, link1.cget("font"))
        f.configure(underline = True, size=9)
        link1.configure(font=f)
        link1.bind("<Button-1>", self.on_btnParams_click)

        btnCancel = Button(btnFrame, text='Отмена', width=12, command=self.on_btnCancel_click)
        btnCancel.pack(side=RIGHT)

        btnOk = Button(btnFrame, text='OK', width=12, command=self.on_btnOk_click)
        btnOk.pack(side=RIGHT, padx=10,)

        #########################################################################
        paramsFrame = Frame(parent, )#borderwidth=2, relief='groove')
        paramsFrame.pack(fill=X, padx=30, pady=0,)

        emptyFrame1 = Frame(paramsFrame, )#borderwidth=2, relief='groove')
        emptyFrame1.pack(fill=X, padx=0, pady=15,)

        # printer ----------------------------------------------------------------
        #printerFrame = Frame(paramsFrame)
        printerFrame = LabelFrame(paramsFrame, text='Печать', padding=5)
        printerFrame.pack(fill=X, padx=0, pady=7,)

        #printerLabel = Label(printerFrame, text="Принтер:", width=15, )
        #printerLabel.pack(side=LEFT)

        prn_i = 0
        prn = config.get('printer', None)
        if prn and all_printers.count(prn) > 0:
            prn_i = all_printers.index(prn)
        self.printerInput = Combobox(printerFrame, values = all_printers, state='readonly')
        self.printerInput.current(prn_i)
        self.printerInput.pack(fill=X, expand=True)
        
        # sharing ----------------------------------------------------------------
        sharingFrame = LabelFrame(paramsFrame, text='Диски и каталоги', padding=5)
        sharingFrame.pack(fill=X,)

        sharingBtnsFrame = Frame(sharingFrame)
        sharingBtnsFrame.pack(side=LEFT,anchor=N, )

        sharingBtnAdd = Button(sharingBtnsFrame, text='Добывить', width=12, command=self.on_btnSharingAdd_click, )
        sharingBtnAdd.pack()

        sharingBtnDel = Button(sharingBtnsFrame, text='Удалить', width=12, command=self.on_btnSharingDel_click, )
        sharingBtnDel.pack()

        sharingListFrame = Frame(sharingFrame)
        sharingListFrame.pack(fill=X, expand=True)

        self.sharingList = Listbox(sharingListFrame, height=6, selectmode=SINGLE)
        self.sharingList.pack(fill=BOTH, expand=True)

        shares = config.get('shares')
        if shares != None:
            for shr in shares:
                if shr == None or shr == '':
                    continue
                self.sharingList.insert(END, shr)
            pass

        pass


    ################################################################################################
    ################################################################################################


    def on_btnParams_click(self,e):
        if self.paramsShowed:
            self.root.geometry("350x270")
            pass
        else:
            self.root.geometry("430x460")
            pass

        self.paramsShowed = not self.paramsShowed
        pass


    def on_btnSharingAdd_click(self):
        dirname = filedialog.askdirectory()
        self.sharingList.insert(END, dirname)
        pass


    def on_btnSharingDel_click(self):
        try:
            index = self.sharingList.curselection()[0]
            self.sharingList.delete(index)
        except IndexError:
            pass
        pass

    def on_btnOk_click(self):
        self.showStatusModal()
        if self.onOk:
            prn = self.printerInput.get()
            if prn == PRN_NOT_USE:
                prn = None
            shr = self.sharingList.get(0,END)
            self.onOk(username=self.username.get(), passwd=self.passwd.get(), printer=prn, shares=shr)
        pass

    def on_btnCancel_click(self):
        if self.onCancel:
            self.onCancel()
        pass

    def on_statusModal_btnClancel_click(self):
        self.closeStatusModal()
        pass

    def on_wnd_delete(self):
        self.on_btnCancel_click()
        pass

    def on_keyEsc(self, event):
        #if self.toplevel_dialog:
        #    self.on_statusModal_btnClancel_click()
        #else:
        self.on_btnCancel_click()
        pass

    def on_keyReturn(self, event):
        if not self.toplevel_dialog:
            self.on_btnOk_click();
            #print('key_enter')
        pass

    pass
