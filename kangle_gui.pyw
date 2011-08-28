#! /usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2-clause BSD

from Tkinter import *
import tkFileDialog
import thread
from threading import Timer
from kangle import Kangle

# TODO: advanced mode
#       add all modes and featues
#       info box
#       better concurrency
#       alternative GUI(QT)

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2011, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.2"

class Kangle_GUI():
    
    def __init__(self):
        self.window = Tk(className="Kangle GUI")
        self.window.resizable(False, False)
        self.window.ml = Menu(self.window)
        self.window.ml.add_command(label="Simple mode", command=self.menu)
        self.window.config(menu=self.window.ml)
        
        self.label1 = Label(self.window, text="Title: ", pady=10)
        self.label1.grid(row=0,column=0)
        self.title = StringVar()
        self.entry1 = Entry(self.window, textvariable=self.title)
        self.title.set('Sample')
        self.entry1.grid(row=0, column=1)
        
        self.label2 = Label(self.window, text="Kindle dir: ", pady=10)
        self.label2.grid(row=1, column=0)
        self.kindledir = StringVar()
        self.entry2 = Entry(self.window,textvariable=self.kindledir)
        self.kindledir.set('E:\\')
        self.entry2.grid(row=1, column=1)
        self.button1 = Button(master=self.window, text="...", command=self.target)
        self.button1.grid(row=1, column=2, padx=10)
         
        self.label3 = Label(self.window, text="Source dir: ", pady=10)
        self.label3.grid(row=2, column=0)
        self.sourcedir = StringVar()
        self.entry3 = Entry(self.window, textvariable=self.sourcedir)
        self.sourcedir.set('C:\\pictures')
        self.entry3.grid(row=2, column=1)
        self.button2 = Button(master=self.window, text="...", command=self.source)
        self.button2.grid(row=2, column=2, padx=10)
        
        self.starter = StringVar()
        self.button2 = Button(master=self.window, text="Start", command=self.starttimer, 
            padx=50, textvariable=self.starter)
        self.starter.set("Start")
        self.button2.grid(row=3, column=1)
        
        self.advanced = False
        self.ready = False
        self.label4 = Label(master=self.window, text='', relief=SUNKEN, width=50)
        self.label4.grid(sticky="w", columnspan=3, pady=5)
        self.window.mainloop()
     
    def starttimer(self):
        if not self.ready:
            Timer(0.1, self.start).start()
        else:
            thread.exit()
            self.ready = True
        
    def start(self):
        self.starter.set("Stop")
        kangle = Kangle(self.title.get(), self.kindledir.get(), 
            self.sourcedir.get())    
        self.ready = False
        thread.start_new_thread(self.run, (kangle, ))
        while True:
            str = "%d/%d" % (kangle._counter, kangle._amount)
            self.label4.config(text=str)
            if self.ready:
                break
        self.starter.set("Start")
        self.label4.config(text="")
        self.ready = False

    def run(self, kangle):
        kangle.run()
        self.ready = True
        
    def source(self):
        dirname = tkFileDialog.askdirectory(parent=self.window,
            initialdir=self.sourcedir.get(), 
            title="Please select the source directory")
        self.sourcedir.set(dirname)
    
    def target(self):    
        dirname = tkFileDialog.askdirectory(parent=self.window,
            initialdir=self.kindledir.get(), 
            title='Please select the kindle root directory')
        self.kindledir.set(dirname)
        
    def menu(self):
        if self.advanced:
            text = "Simple mode"
            self.advanced = False
        else:
            text = "Advanced mode"
            self.advanced = True
        self.window.ml.entryconfigure(1,label=text)
    
if __name__ == "__main__":
    kangle_gui = Kangle_GUI()    