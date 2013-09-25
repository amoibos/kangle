#! /usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2-clause BSD

from Tkinter import Label, Entry, StringVar, Menu, Button, SUNKEN, Tk
from os.path import exists
import tkFileDialog
from thread import exit, start_new_thread
from threading import Timer
from kangle import Kangle

# TODO: advanced mode
#       add all modes and featues
#       info box
#       better concurrency
#       alternative GUI(QT)

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2013, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.2.1"

class Kangle_GUI(object):
    def __init__(self):
        self.window = Tk(className='Kangle %s' % __version__)
        self.window.resizable(False, False)
        self.window.ml = Menu(self.window)
        self.window.ml.add_command(label="Simple mode", command=self.menu)
        self.window.config(menu=self.window.ml)
        
        self.titlecaption = Label(self.window, text="Title: ", pady=10)
        self.titlecaption.grid(row=0,column=0)
        self.title = StringVar()
        self.titlefield = Entry(self.window, textvariable=self.title, bd=5)
        self.title.set("Sample")
        self.titlefield.grid(row=0, column=1)
        
        self.kindledircaption = Label(self.window, text="Kindle dir: ", pady=10)
        self.kindledircaption.grid(row=1, column=0)
        self.kindledir = StringVar()
        self.targetfield = Entry(self.window,textvariable=self.kindledir, bd=5)
        self.kindledir.set("E:\\")
        self.targetfield.grid(row=1, column=1)
        self.kindlebrowser = Button(master=self.window, text="...", command=self.target)
        self.kindlebrowser.grid(row=1, column=2, padx=10)
         
        self.sourcedircaption = Label(self.window, text="Source dir: ", pady=10)
        self.sourcedircaption.grid(row=2, column=0)
        self.sourcedir = StringVar()
        self.sourcefield = Entry(self.window, textvariable=self.sourcedir, bd=5)
        self.sourcedir.set(r"C:\pictures")
        self.sourcefield.grid(row=2, column=1)
        self.sourcebrowser = Button(master=self.window, text="...", command=self.source)
        self.sourcebrowser.grid(row=2, column=2, padx=10)
        
        self.starter = StringVar()
        self.startbutton = Button(master=self.window, text="Start", command=self.starttimer, 
            padx=50, textvariable=self.starter)
        self.starter.set("Start")
        self.startbutton.grid(row=3, column=1)
        
        self.advanced = self.ready = False
        self.progressbar = Label(master=self.window, text="", relief=SUNKEN, width=60)
        self.progressbar.grid(sticky="w", columnspan=3, pady=5)
        self.window.mainloop()
     
    def starttimer(self):
        if not self.ready:
            Timer(0.1, self.start).start()
        else:
            exit()
            self.ready = True
        
    def start(self):
        #path check
        if not exists(self.kindledir.get()) or not exists(self.sourcedir.get()):
            return
        self.starter.set("Stop")
        kangle = Kangle(self.title.get(), self.kindledir.get(), 
            self.sourcedir.get())    
        self.ready = False
        start_new_thread(self.run, (kangle,))
        while True:
            self.progressbar.config(text="%d/%d" % (kangle._counter, kangle._amount))
            if self.ready:
                break
        self.starter.set("Start")
        self.progressbar.config(text="")
        self.ready = False

    def run(self, kangle):
        kangle.looking(self.kindledir.get())
        self.ready = True
        
    def source(self):
        dirname = tkFileDialog.askdirectory(parent=self.window,
                                                        initialdir=self.sourcedir.get(), 
                                                        title="Please select the source directory")
        self.sourcedir.set(dirname)
    
    def target(self):    
        dirname = tkFileDialog.askdirectory(parent=self.window,
                                                        initialdir=self.kindledir.get(), 
                                                        title="Please select the kindle root directory")
        self.kindledir.set(dirname)
        
    def menu(self):
        self.advanced = not self.advanced
        text = "Simple mode" if self.advanced else "Advanced mode"
        self.window.ml.entryconfigure(1,label=text)
    
if __name__ == "__main__":
    kangle_gui = Kangle_GUI()    
    