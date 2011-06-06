#! /usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2-clause BSD

from Tkinter import *
import tkFileDialog
from kangle import Kangle

# TODO: advanced mode, threading for status bar, bugs(from console)
__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2011, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.1"

class Kangle_GUI():
    
    def __init__(self):
        self.window = Tk(className="Kangle GUI")
        self.window.ml = Menu(self.window)
        self.window.ml.m = Menu(self.window.ml, tearoff=0)
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
        
        self.button2 = Button(master=self.window, text="Start", command=self.run, 
            padx=50)
        self.button2.grid(row=3, column=1)
        self.advanced = False
        self.window.mainloop()
        
    def run(self):
        self.button2.config(state=DISABLED)
        kangle = Kangle(self.title.get(), self.kindledir.get(), 
            self.sourcedir.get())    
        kangle.run()
        self.button2.config(state=NORMAL)
    
    def source(self):
        dirname = tkFileDialog.askdirectory(parent=self.window,
            initialdir=self.sourcedir.get(), 
            title='Please select the source directory')
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