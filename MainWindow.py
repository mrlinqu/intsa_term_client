from tkinter import *
#import tempfile
import threading
#import time
import logging

class MainWindow(threading.Thread):
	wnd = None
	login = None
	password = None
	input_login = None
	input_password = None
	btnOk = None
	btnCancel = None
	bntOk_pressed = False
	statusText = None

	
	def __init__(self, config={}):
		super(MainWindow, self).__init__()
		#threading.Thread.__init__(self)

		self.config = config


	def createWindow(self, root):
		#		ICON = (b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x08\x00h\x05\x00\x00'
#			b'\x16\x00\x00\x00(\x00\x00\x00\x10\x00\x00\x00 \x00\x00\x00\x01\x00'
#			b'\x08\x00\x00\x00\x00\x00@\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
#			b'\x00\x01\x00\x00\x00\x01') + b'\x00'*1282 + b'\xff'*64
#
#		_, ICON_PATH = tempfile.mkstemp()
#		with open(ICON_PATH, 'wb') as icon_file:
#			icon_file.write(ICON)

		
		root.title("Insta : Подключение к удаленному рабочему столу")
#		root.iconbitmap(default=ICON_PATH)

		wnd_w = 370
		wnd_h = 240
		wnd_x = int(root.winfo_screenwidth()/2 - wnd_w/2)
		wnd_y = int(root.winfo_screenheight()/2 - wnd_h/2)
		root.geometry('%sx%s+%s+%s' % (wnd_w, wnd_h, wnd_x, wnd_y))
		root.resizable(False, False)

		self.login = StringVar()
		self.login.set(self.config.get('login',''))
		self.passwd = StringVar()

		label_logo1 = Label(root, text="Подключение к удаленному\nрабочему столу", justify='left', font='arial 14').place(x=45,y=20)

		label_login = Label(root, text='Пользователь:').place(x=45,y=100)
		self.input_login = Entry(root, width=30, textvariable=self.login)
		self.input_login.place(x=145,y=100)
		label_password = Label(root, text='Пароль:').place(x=45,y=136)
		self.input_password = Entry(root, width=30, textvariable=self.passwd, show="●")
		self.input_password.place(x=145,y=136)

		#frame1 = Frame(root, bd=2, width=100, height=100, relief='groove').place(x=30,y=30)
		self.statusText = StringVar()
		label_status = Label(root, text='', width=40, justify='center', textvariable=self.statusText).place(x=45,y=165)

		#self.btnOk = Button(root, text='OK', width=10, height=1, command=self.on_btnOk_click).place(x=120,y=172)
		#self.btnCancel = Button(root, text='Cancel', width=10, height=1, command=self.on_btnCancel_click).place(x=210,y=172)
		self.btnOk = Button(root, text='OK', width=10, height=1, command=self.on_btnOk_click)
		self.btnOk.place(x=160,y=200)
		self.btnCancel = Button(root, text='Отмена', width=10, height=1, command=self.on_btnCancel_click)
		self.btnCancel.place(x=250,y=200)

		root.bind("<Escape>", self.on_keyEsc)
		root.bind("<Return>", self.on_keyReturn)
		root.protocol("WM_DELETE_WINDOW", self.on_closing)

		if not self.login.get():
			self.input_login.focus_set()
		else:
			self.input_password.focus_set()
		#self.InputText.bind('<Return>', self.return_key)

	def on_closing(self):
		#root.destroy()
		self.on_btnCancel_click()
		pass


	def on_keyEsc(self, event):
		self.on_btnCancel_click()
		#self.wnd.quit()
		pass


	def on_keyReturn(self, event):
		self.on_btnOk_click()
		pass


	def on_btnOk_click(self):
		#self.bntOk_pressed = True
		#self.wnd.quit()
		#while 1:
			#pass

		#self.wnd.withdraw()
		#self.wnd.deiconify()
		if self.onOk:
			self.onOk(login=self.login.get(), passwd=self.passwd.get())
		pass


	def on_btnCancel_click(self):
		#self.wnd.quit()
		if self.onCancel:
			self.onCancel()

		pass


	def run(self):
		logging.debug('main window thread id: %s',threading.get_ident())
		self.wnd = Tk()
		self.createWindow(self.wnd)
		#self.wnd.after_idle(self.tick)
		self.wnd.mainloop()

		#if(self.bntOk_pressed):
		#	return (self.login.get(), self.passwd.get())
		#else:
			#return

#	def stop(self):
#		pass


	def close(self):
		self.wnd.quit()
		pass


	def setStatus(self, text):
		self.statusText.set(text)
		pass

	def setState(self, state):
		self.input_login.config(state=state)
		self.input_password.config(state=state)
		self.btnOk.config(state=state)
		pass

	def lock(self):
		self.setState('disabled')
		pass

	def unlock(self):
		self.setState('normal')
		pass
