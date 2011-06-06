#! /usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2-clause BSD

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
__version__ = "0.5.4"

# Kangle, a symbiosis of manga and kindle
class Kangle(object):
    """Kangle makes manga scans readable on a kindle device."""
    supportedFormats = ['.jpg', '.png', '.gif', '.bmp']
    
    def run(self):
        self._looking()

    # kindle reads the files in order of timestamp
    def adjustImage(self, filename, counter):
        """Adjust the image file filename to kindle screen and use counter
        for naming."""
        first = Image.open(filename)
        # resolution of the image
        (width, height) = first.size
        filename = '%05da%s' % (counter, filename[-4:])
        # too wide, better splitting in middle
        if self.splitting and width > height:
            # take the second half and resize
            second = first.crop((width / 2, 0, width, height))
            first = first.crop((0, 0, width / 2, height))
            # reverse: manga reading style, right to left
            # save in correct order
            if not self.reverse:
                first, second = second, first
            self._save(second, filename)
            filename = filename.replace("a", "b")
        self._save(first, filename)
        
    def _save(self, image, filename):
        """Save the image with the enabled options under the filename."""
        if self.stretching:
            image = image.resize(self.resolution)
        if self.footer:
            text = "%s/%05d@%s" % (filename[:-4], self._amount, self.title)
            self._makeFootnote(image, text)
        fullName = join(self._target_dir, filename)
        image.save(fullName)
            
    def _makeFootnote(self, image, text):
        """Write the text downright."""
        draw = ImageDraw.Draw(image)
        width, height = draw.textsize(text)
        x, y = image.size[0] - width, image.size[1] - height
        fore, back = 0, "white"
        try:
            back = image.info["transparency"]
        except KeyError:
            if image.mode == "P":
                palette = sorted(image.getcolors(), key=lambda color:color[0])
                fore, back = palette[-2][1], palette[-1][1]
        draw.rectangle((x, y, image.size[0], image.size[1]), fill=back)
        draw.text((x, y), text, fill=fore)
        
    # optimized recursive search
    def _looking(self):
        """Find supported pictures in dir."""
        for curr_dir, dirs, files in walk(self._dir):
            dirs.sort()
            files.sort()
            for filename in files:
                # filter for file extensions, 
                # this must be supported by PIL
                if filename[-4:].lower() in Kangle.supportedFormats:
                    fullName = join(curr_dir, filename)
                    self.adjustImage(fullName, self._counter)
                    self._counter += 1  
    
    def _amountFiles(self):
        """Count amount of supported Files in dir and subdirectories."""
        amount = 0
        for _, _, files in walk(self._dir):
            for filename in files:
                # filter for file extensions, 
                # this must be supported by PIL
                if filename[-4:].lower() in Kangle.supportedFormats:
                    amount += 1
        return amount
    
    def __init__(self, title, target_dir, source, counter=0):
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
        self._dir = source
        # count number of supported Files
        if self.footer:
            self._amount = self._amountFiles()
        for dir in ["pictures", title]:
            self._target_dir = join(self._target_dir, dir)
            if not isdir(self._target_dir):
                mkdir(self._target_dir)
            elif dir != "pictures":
                print >> stderr, "directory ", dir, " already exists"

if __name__ == "__main__":
    try:
        # sys.argv[2] could look like "D:\"(windows) or "/media/kindle"(unix)
        title, target_dir = argv[1], argv[2]
    except IndexError:
        if len(argv) > 1 and argv[1] == "--version":
            print "Kangle version ", __version__," by ", __author__
            print "Thanks to", __credits__
            exit(0) 
        else:
            print >> stderr, "arguments: <TITLE> <KINDLE_ROOT_DIRECTORY>"
            exit(-1)
    kangle = Kangle(title, target_dir, getcwd())    
    print "found", kangle._amount, "files"
    print "converting & transferring ...",
    kangle.run()
    print "finished"
