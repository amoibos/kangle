#! /usr/bin/env python

# Copyright 2011 Daniel Oelschlegel. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions 
# are met:
#
#   1. Redistributions of source code must retain the above copyright 
#   notice, this list of conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright 
#   notice, this list of conditions and the following disclaimer in the 
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY Daniel Oelschlegel ``AS IS'' AND ANY 
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL Daniel Oelschlegel OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR 
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY 
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of Daniel Oelschlegel.


# this program requires a plugged kindle, at least python 2.* and PIL
# start this program in a subdirectory that contains picture files or 
# directories
# press [ALT] + [z] for rereading the entries in pictures on a kindle

# kindle tip: [ALT] + [f] = fullscreen, 2x [ALT] + [p] clear the boundary

from sys import exit, argv, stderr
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
__version__ = "0.5.2"

# Kangle, a symbiosis of manga and kindle
class Kangle(object):
    """Kangle makes manga scans readable on a kindle device."""
    
    def run(self, dir):
        self.looking(dir)

    # kindle reads the files in order of timestamp
    def adjustImage(self, filename, counter, extension):
        """Adjust the image file filename to kindle screen and use counter
        for naming."""
        first = Image.open(filename)
        # resolution of the image
        (width, height) = first.size
        filename = '%06da%s' % (counter, extension)
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
            filename = filename.replace('a', 'b')
        self.save(first, filename)
        
    def save(self, image, filename):
        """Save the image with the enabled options under the filename."""
        if self.stretching:
            image = image.resize(self.resolution)
        if self.footer:
            self.makeFootnote(image, '%s@%s' % (filename, self.title))
        fullName = join(self._target_dir, filename)
        image.save(fullName)
            
    def makeFootnote(self, image, text):
        """Write the text downright."""
        draw = ImageDraw.Draw(image)
        width, height = draw.textsize(text)
        x, y = image.size[0] - width, image.size[1] - height
        try:
            back = image.info['transparency']
        except KeyError:
            back = "white"
        draw.rectangle((x, y, image.size[0], image.size[1]), fill=back)
        draw.text((x, y), text, fill=0)
        
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
                extension = filename[-4:].lower()
                if extension in ['.jpg', '.png', '.gif', '.bmp']:
                    fullName = join(curr_dir, filename)
                    self.adjustImage(fullName, counter, extension)
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
        self.footer = True
        # for resuming a session
        self._counter = counter
        # resolution of your kindle, required for stretching
        self.resolution = (600, 800)
        self.title = title
        self._target_dir = target_dir
        for dir in ["pictures", title]:
            self._target_dir = join(self._target_dir, dir)
            if not isdir(self._target_dir):
                mkdir(self._target_dir)
            elif dir == argv[1]:
                print >> stderr, "directory ", dir, " already exists"

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
            print >> stderr, "arguments: <TITLE> <KINDLE_ROOT_DIRECTORY>"
            exit(-1)
    kangle = Kangle(title, target_dir)    
    print "converting & transferring ...",
    kangle.run(getcwd())
    print "finished"