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
# THIS SOFTWARE IS PROVIDED BY Daniel Oelschlegel ``AS IS'' AND ANY EXPRESS OR
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

# kindle tip: [ALT] + [f] = fullscreen, 2x [ALT] + [p] clear the boundary

from sys import exit, argv
from os import walk, mkdir, getcwd
from os.path import join, isdir

try:
    from PIL import Image, ImageDraw
except ImportError:
    print "please install PIL"
    exit(-2)

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2011, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.5"

# Kangle, a symbiosis of manga and kindle
class Kangle(object):
    """Kangle makes manga scans readable on a kindle device."""
    
    def run(self, dir):
        print "converting & transferring ...",
        self.looking(dir)
        print "finished"

    # kindle reads the files in order of timestamp
    def adjustImage(self, filename, counter):
        """Adjust the image file filename to kindle screen and use counter
        for naming."""
        first = Image.open(filename)
        # resolution of the image
        (width, height) = first.size
        filename = '%06da.jpg' % counter
        # too wide, better splitting in middle
        if self.splitting and width > height:
            # take the second half and resize
            second = first.crop((width / 2, 0, width, height))
            first = first.crop((0, 0, width / 2, height))
            # reverse: manga reading style, right to left
            # save in correct order
            if not self.reverse:
                first, second = second, first
            self.save(second, filename)
            filename = filename.replace('a.jpg', 'b.jpg')
        self.save(first, filename)
        
    def save(self, image, filename):
        """Save the image with the enabled options under the filename."""
        if self.stretching:
            image = image.resize(self.resolution)
        if self.footer:
            self.makeFootnote(image, '%s@%s' % (filename, self.title))
        fullName = join(self._target_dir, filename)
        # prevents IOError with this type,convert is often unnecessary and slow
        if not image.mode in ['P']:
            image.save(fullName, "JPEG")
        else:
            image.convert("RGB").save(fullName, "JPEG")
    
    def makeFootnote(self, image, text):
        """Write the filename@Title downright."""
        draw = ImageDraw.Draw(image)
        dim = draw.textsize(text)
        x1, y1 = image.size[0] - dim[0], image.size[1] - dim[1]
        draw.rectangle((x1,y1, image.size[0], image.size[1]), fill='white')
        draw.text((x1, y1), text, fill='black')

    # optimized recursive search
    def looking(self, dir):
        """Find supported pictures in dir."""
        counter = self._counter
        for curr_dir, dirs, files in walk(dir):
            dirs.sort()
            files.sort()
            for filename in files:
                # filter for file extensions, 
                # this must be supported by PIL
                if filename[-4:].lower() in ['.jpg', '.png', '.gif']:
                    fullName = join(curr_dir, filename)
                    self.adjustImage(fullName, counter)
                    counter += 1  
        self._counter = counter
        
    def __init__(self, title, target_dir, counter=0):
        # reverse order by splitted image, usefull for reading manga
        # comics should use reverse = False
        self.reverse = True
        # splitting if the image is too wide
        self.splitting = True
        # stretching
        self.stretching = True
        # footnote displays the name of the image file
        self.footer = True#False
        # needed for recursive search
        self._counter = counter
        # resolution of your kindle, required for stretching
        self.resolution = (600, 800)
        self.title = title
        self._target_dir = target_dir
        for dir in ["pictures", title]:
            self._target_dir = join(self._target_dir, dir)
            if not isdir(self._target_dir):
                print "creating directory " , self._target_dir
                mkdir(self._target_dir)
            elif dir == argv[1]:
                print "directory ", dir, " already exists"

if __name__ == "__main__":
    try:
        # sys.argv[2] could look like "D:\"(windows) or "/media/kindle"(unix)
        title, target_dir = argv[1], argv[2]
    except IndexError:
        if len(sys.argv) > 1 and sys.argv[1] == "--version":
            print "Kangle version ", __version__," by ", __author__
            print "Thanks to", __credits__
            exit(0) 
        else:
            print "arguments: <TITLE> <KINDLE_ROOT_DIRECTORY>"
            exit(-1)
   
    kangle = Kangle(title, target_dir)    
    kangle.run(getcwd())
    