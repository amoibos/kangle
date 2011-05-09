#! /usr/bin/env python

# Copyright 2011 Daniel Oelschlegel. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright 
#   notice, this list of conditions and the following disclaimer in the 
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN
# NO EVENT SHALL Daniel Oelschlegel OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF 
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Daniel Oelschlegel.


# this program requires a plugged kindle, at least python 2.* and PIL
# start this program in a subdirectory that contains picture files or 
# directories
# press [ALT] + [z] for rereading the entries in pictures on a kindle

# kindle tip: [ALT] [f] = fullscreen, 2x [ALT] [p] clear the boundary

import sys
import os
try:
    import Image
except ImportError:
    print "please install PIL"
    sys.exit(-2)

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2011, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.3"

class Kangle(object):
    """Kangle makes manga scans readable on a kindle device."""
    # reverse order splitted image, usefull for manga reading style
    # comics often should use reverse = False instead of manga
    reverse = True
    # splitting if the image is too wide
    splitting = True
    # needed for recursive search
    _counter = 0
    # resolution of your kindle, required for stretching
    resolution = (600, 800)
    # target_dir is the kindle root directory, dummy value
    _target_dir = 'D:\\'

    def resetCounter(self):
        self._counter = 0

    def run(self, dir):
        self.resetCounter()
        print "converting & transferring ...",
        self.looking(dir)
        print "finished"

    # kindle reads the files in order of timestamp
    def adjustImage(self, filename, counter):
        """Adjust the image file filename to kindle screen and use counter for naming."""
        first = Image.open(filename)
        # prevents IOError with this type, convert is often unnecessary and slow
        palleteMode = first.mode == 'P'
        # resolution of the image
        (width, height) = first.size
        filename = '%06da.jpg' % self._counter
        # too wide, better splitting in middle and stretching
        if splitting and width > height:
            # take the second half and resize
            second = first.crop((width / 2, 0, width, height))
            second = second.resize(self.resolution)
            first = first.crop((0, 0, width / 2, height))
            fullName = os.path.join(self._target_dir, filename)
            # reverse : manga reading style, right to left, save in correct order
            if not reverse:
                first, second = second, first.resize(self.resolution)
            if not palleteMode:
                second.save(fullName, "JPEG")
            else:
                second.convert("RGB").save(fullName, "JPEG")
            filename = filename.replace('a.jpg', 'b.jpg')
        first = first.resize(self.resolution)
        fullName = os.path.join(self._target_dir, filename)
        if not palleteMode:
            first.save(fullName, "JPEG")
        else:
            first.convert("RGB").save(fullName, "JPEG")

    # optimized recursive search
    def looking(self, dir_name):
        """Find supported pictures in dir_name."""
        dirs = []
        files = []
        for item in os.listdir(dir_name):
            item = os.path.join(dir_name, item)
            if os.path.isdir(item):
                dirs.append(item)
            else:
                files.append(item)
        # some OSes need this, additional sorting
        files.sort()
        for filename in files:
            # filter for file extensions, 
            # this must be supported by PIL
            if filename[-4:].lower() in ['.jpg', '.png', '.gif']:
                self.adjustImage(filename, self._counter)
                self._counter += 1
        # continue with subdirectories
        for dir in dirs:
            self.looking(dir)

    def __init__(self, title, target_dir):
        self._target_dir = target_dir
        for dir in ["pictures", title]:
            self._target_dir = os.path.join(self._target_dir, dir)
            if not os.path.isdir(self._target_dir):
                print "creating directory " , self._target_dir
                os.mkdir(self._target_dir)
            elif dir == sys.argv[1]:
                print "directory ", dir, " already exists"

if __name__ == "__main__":
    try:
        # sys.argv[2] could look like "D:\"(windows) or "/media/kindle"(unix)
        title, target_dir = sys.argv[1], sys.argv[2]
    except IndexError:
        if len(sys.argv) > 1 and sys.argv[1] == "--version":
            print "Kangle version ", __version__," by ", __author__
            print "Thanks to", __credits__
            sys.exit(0) 
        else:
            print "arguments: <TITLE> <KINDLE_ROOT_DIRECTORY>"
            sys.exit(-1)
   
    kangle = Kangle(title, target_dir)    
    kangle.run(os.getcwd())
    