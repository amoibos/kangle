#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2-clause BSD

# this program requires a plugged kindle, at least python 2.5 and PIL
# start this program in a subdirectory that contains picture files or
# directories
# press [ALT] + [z] for rereading the entries in pictures on a kindle
# kindle tip: [ALT] + [f] = fullscreen,  [ALT] + [p] clear the boundary

from PIL import Image, ImageDraw, ImageFilter
from sys import exit, argv, stderr, stdout
from os import walk, mkdir, getcwd
from os.path import join, isdir, getsize, splitext
from glob import glob
from zipfile import ZipFile
from getopt import getopt
import re
from threading import Timer
import tempfile
import shutil
import zlib
#from thread import start_new_thread

## PDF Extraktion
## GUI(TK) 
## Kommandozeilenparameter(Standard abaendern+Parameter info)
## Buildskript und EXE beilegen
## Viewer Testmode

import cProfile


# getopt or config parser for standalone program behavior
# TODO: BUG image file is truncated (0 bytes not processed)
#        convert('L')

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2013, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.8.2"

# Kangle, a symbiosis of manga and kindle
class Kangle(object):
    """Kangle makes manga scans readable on a kindle device."""
    supportedFormats = ('.jpg', '.png', '.gif', '.bmp')
    
    def progress(self, firstRun=False):
        """Call every 30s this function for printing the progress on screen"""
        if self.timerActivated:
            self._thread = Timer(30, self.progress)
            self._thread.start()
            if not firstRun:
                percent = 100 * self._counter / self._amount
                if percent not in self._progress:
                    sys.stdout.write("\r %s" % percent)
                    sys.stdout.flush()
                    self._progress[percent] = True
        
    def start(self):
        self.progress(True)
        self.looking(self._dir)
        self._thread.cancel()

    # TODO: poly. instead of linear searching(similar to binary search)
    def _cropping(self, image):
        """Crops one color border from scanned image"""
        # bad, needed better filter
        img = image.convert('L').filter(ImageFilter.MaxFilter(size=5))
        width, height = image.size
        # for loops, every side(w,e,n,s : (parameter index, direction))
        direction = (   (2, 1), (0, -1), 
                        (3, 1), (1, -1))
        # regions for checks, start region + end position
        # max 20 percent border cut for each side
        box = ( [0, 0, 0, height],
                [width, 0, width, height],
                [0, 0, width, 0],
                [0, height, width, height] )
        diff = []
        dim = (width, width, height, height)
        
        for side, _ in enumerate(direction):
            cnt = 0
            while cnt < dim[side]:
                idx = direction[side]
                box[side][idx[0]] += idx[1]
                # cut (increasing) region
                border = img.crop(box[side])
                colorCnt = len(border.getcolors())
                if colorCnt > 1:
                    colors = border.getcolors()
                    base = colors[0][1]
                    sum = 0
                    secondChance = True
                    for color in colors:
                        if abs(base - color[1]) > 6:
                            secondChance = False
                            break
                    if not secondChance:
                        diff.append(cnt)
                        break
                cnt += 1
                
            # for one color pages
            if cnt + 1 >= dim[side]:
                return image
        return image.crop((0+diff[0], 0+diff[2], 
            width-diff[1], height-diff[3]))
    
    # kindle reads the files in order of timestamp
    def adjust_image(self, file_name, counter):
        """Adjusts the image file file_name to kindle screen and use counter for naming."""
        try:
            first = Image.open(file_name)
        except IOError:
            print >> stderr, "damaged image file: %s" % self.file_name
            if self.skipping:
                return
            exit(-3)
        # for more readability
        if self.cropping:
            first = self._cropping(first)
        # resolution of the image
        (width, height) = first.size
        file_name = '%05da%s' % (counter, splitext(file_name)[1])
        # too wide, better splitting in middle
        if self.splitting and width > height:
            # take the second half and resize
            second = first.crop((width / 2, 0, width, height))
            first = first.crop((0, 0, width / 2, height))
            # reverse: manga reading style, right to left
            # save in correct order
            if not self.reverse:
                first, second = second, first
            self._save(second, file_name)
            file_name = file_name.replace("a", "b")
        self._save(first, file_name)
        
    def _save(self, image, file_name):
        """Saves the image with the enabled options under the file_name."""
        if self.stretching:
            # for better quality
            try:
                image = image.convert("RGB")
            except IOError:
                # ups, something went wrong
                pass
            image = image.resize(self.resolution, Image.BILINEAR)
        
        if self.footer:
            text = self.signature[0] % tuple(map(eval, self.signature[1]))
            self._make_footnote(image, text)
        full_name = join(self._target_dir, file_name)
        #saving in right order, synchronication?
        #start_new_thread(image.save, (full_name, ))       
        image.save(full_name)
        
    def _make_footnote(self, image, text):
        """Writes the text downright."""
        draw = ImageDraw.Draw(image)
        if self._x is None:
            width, height = draw.textsize(text)
            self._x, self._y = image.size[0] - width, image.size[1] - height
        fore, back = 0, "white"
        if  "transparency" in image.info:
            back = image.info["transparency"]
        else:
            if image.mode == "P":
                palette = sorted(image.getcolors(), key=lambda color:sum(color))
                if len(palette) > 1:
                    fore, back = palette[0][1], palette[-1][1]
                
        draw.rectangle((self._x, self._y, image.size[0], image.size[1]), fill=back)
        draw.text((self._x, self._y), text, fill=fore)
    
    def _double(self, file_name):
        """Find doubles"""
        fileSize = getsize(file_name)
        for element in Image.open(file_name).getdata():
            hash_code = zlib.crc32(str(element))   
        if fileSize not in self._duplicate:
            self._duplicate[fileSize] = {hash_code: True}
            return False
        if hash_code in self._duplicate[fileSize]:
            return True
        self._duplicate[fileSize][hash_code] = True
        return False    
        
    def _num_sort(self, fileList):
        backup = fileList[:]
        try:
            fileList.sort(cmp, key=lambda tFile: float(self.numPattern.search(tFile).group(0)))
        except AttributeError:
            fileList = backup
        return fileList    
        
    # optimized recursive search
    def looking(self, dir):
        """Finds supported pictures in dir."""
        for curr_dir, dirs, files in walk(unicode(dir)):
            dirs = [dir.encode("utf-8").lower() for dir in dirs]
            dirs = self._num_sort(dirs) if self.num_sort else sorted(dirs)
            files = [f.encode("utf-8").lower() for f in files]
            files = self._num_sort(files) if self.num_sort else sorted(files)
            dirs, files = [item.decode("utf-8") for item in dirs],  [item.decode("utf-8") for item in files]
            for file_name in files:
                # filter for file extensions, 
                # this must be supported by PIL
                self.file_name = file_name
                full_name = join(curr_dir, file_name)
                file_extension = splitext(file_name)[1].lower()
                if file_extension in ('.zip'):
                    temp_dir = self._temp_dirs[file_name]
                    self.looking(temp_dir)
                    shutil.rmtree(temp_dir)
                elif file_extension in Kangle.supportedFormats:
                    if not self.duplicating and self._double(full_name):
                        self.doubleCounter += 1
                        continue
                    self.adjust_image(full_name, self._counter)
                self._counter += 1
            if not self.deepth:
                break
    
    def _amount_files(self, dir):
        """Counts amount of supported Files in dir and subdirectories."""
        amount = 0
        for _, _, files in walk(unicode(dir)):
            for file_name in files:
                # filter for file extensions, 
                # this must be supported by PIL
                extension = splitext(file_name)[1]
                if extension.lower() in Kangle.supportedFormats:
                    amount += 1
                if extension.lower() in (".zip"):
                    temp_dir = tempfile.mkdtemp()
                    ZipFile(file_name).extractall(temp_dir)
                    self._temp_dirs[file_name] = temp_dir
                    self._amount_files(temp_dir)
            if not self.deepth:
                break
        return amount
  
    def _writeSavePoint(self, target_dir, title, siteno):
        """Writes a resume file for the given title"""
        file_name = glob("%s/pictures/%s/%05d*" % (target_dir, title, siteno))[0]
        with open("%s/pictures/%s.manga_save" % (target_dir, title)) as f:
            f.write("#Fri Sep 02 18:20:13 GMT+01:16 2011")
            f.write("LAST=/mnt/us/pictures/%s/%s" % (title, file_name))
        with open("%s/pictures/%s.manga" % (target_dir, title)) as f:
            f.write("\0")    

    def __init__(self, title, target_dir, source, deepth=True, counter=0):
        # eliminate duplicates
        self.duplicating = True#False
        self._duplicate, self.doubleCounter  = {}, 0
        # useful when scans have too much white borders
        self.cropping = False
        # reverse order by splitted image, usefull for reading manga
        # comics(left to right), manhwa should use reverse = False
        self.reverse = True
        # splitting if the image is too wide
        self.splitting = True
        # stretching
        self.stretching = True
        # displaying useful footer 
        self.footer = True
        # for resuming a session
        self._counter = counter
        # resolution of your kindle, required for stretching
        self.resolution = (600, 800)
        # skipping by damaged images or abort
        self.skipping = True
        self.title = title
        self._target_dir = target_dir
        self._dir = source
        self.deepth = deepth
        self._buffer = []
        self.timerActivated = True
        #for displaying progress in percent and only once
        self._progress = {} 
        self.num_sort = False#True
        self._thread = None
        self._temp_dirs = {}
        # count number of supported Files
        if self.footer:
            self.signature = ("%s/%05d@%s", ("splitext(file_name)[1]", "self._amount", "self.title"))
            self._amount = self._amount_files(self._dir)
            self._x = None
        for dir in ["pictures", title]:
            self._target_dir = join(self._target_dir, dir)
            if not isdir(self._target_dir):
                mkdir(self._target_dir)
            elif dir != "pictures":
                print >> stderr, "directory ", dir, " already exists"
        self.numPattern = re.compile(r'\d+')

if __name__ == "__main__":
    options, remainder = getopt(argv[1:], 'dcrxsh:v', [
                                                         'info',
                                                         'version=',
                                                         ])
    
    try:
        # sys.argv[2] could look like "D:\"(Windows) or "/media/kindle"(Unix-like)
        title, target_dir = argv[1], argv[2]
    except IndexError:
        if len(argv) > 1 and argv[1] == "--version":
            print "Kangle version ", __version__," by ", __author__
            print "Thanks to", __credits__
            exit(0)
        else:
            print >> stderr, "arguments: TITLE KINDLE_ROOT_DIRECTORY <SOURCE>"
            exit(-1)
    source =  argv[3] if len(argv) > 3 else getcwd()
    kangle = Kangle(title, target_dir, source)
    print "found", kangle._amount, "files"
    print "converting & transferring ...",
    if not kangle.duplicating: 
        print "\ndoubles found: ",
    #cProfile.run('kangle.start()')
    kangle.start()
    if not kangle.duplicating: 
        print "%d" % kangle.doubleCounter
    print "finished"
