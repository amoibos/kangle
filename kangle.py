#! /usr/bin/env python

# Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
# License: 2-clause BSD

# this program requires a plugged kindle, at least python 2.* and PIL
# start this program in a subdirectory that contains picture files or
# directories
# press [ALT] + [z] for rereading the entries in pictures on a kindle

# kindle tip: [ALT] + [f] = fullscreen,  [ALT] + [p] clear the boundary
from PIL import Image, ImageDraw, ImageFilter
from sys import exit, argv, stderr
from os import walk, mkdir, getcwd
from os.path import join, isdir, getsize
from glob import glob
import zlib

#import cProfile

# TODO: BUG image file is truncated (0 bytes not processed)
#        convert('L')

# TODO: FEATURE
#       arbitrary footnote strings

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2011, " + __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.7"

# Kangle, a symbiosis of manga and kindle
class Kangle(object):
    """Kangle makes manga scans readable on a kindle device."""
    supportedFormats = ['.jpg', '.png', '.gif', '.bmp']
    
    def run(self):
        self._looking()

    # TODO: poly. instead of linear searching(similar to binary search)
    def _cropping(self, image):
        """Crops one color border from scanned image"""
        # bad, needed better filter
        img = image.convert('L').filter(ImageFilter.MaxFilter(size=5))
        (width, height) = image.size
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
        
        for side in range(len(direction)):
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
    def adjustImage(self, fileName, counter):
        """Adjusts the image file fileName to kindle screen and use counter
        for naming."""
        try:
            first = Image.open(fileName)
        except IOError:
            print "damaged image file"
            if self.skipping:
                return
            exit(-3)
        # for more readability
        if self.cropping:
            first = self._cropping(first)
        # resolution of the image
        (width, height) = first.size
        fileName = '%05da%s' % (counter, fileName[-4:])
        # too wide, better splitting in middle
        if self.splitting and width > height:
            # take the second half and resize
            second = first.crop((width / 2, 0, width, height))
            first = first.crop((0, 0, width / 2, height))
            # reverse: manga reading style, right to left
            # save in correct order
            if not self.reverse:
                first, second = second, first
            self._save(second, fileName)
            fileName = fileName.replace("a", "b")
        self._save(first, fileName)
        
    def _save(self, image, fileName):
        """Saves the image with the enabled options under the fileName."""
        if self.stretching:
            # for better quality
            try:
                image = image.convert("RGB")
            except IOError:
                # ups, something goes wrong
                pass
            image = image.resize(self.resolution, Image.BILINEAR)
        
        if self.footer:
            text = "%s/%05d@%s" % (fileName[:-4], self._amount, self.title)
            self._makeFootnote(image, text)
        fullName = join(self._targetDir, fileName)
        image.save(fullName)
            
    def _makeFootnote(self, image, text):
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
    
    def _double(self, fileName):
        """Find doubles"""
        fileSize = getsize(fileName)
        for element in Image.open(fileName).getdata():
            hashCode = zlib.crc32(str(element))   
        if fileSize not in self._duplicate:
            self._duplicate[fileSize] = {hashCode: True}
            return False
        if hashCode in self._duplicate[fileSize]:
            return True
        self._duplicate[fileSize][hashCode] = True
        return False    
        
    # optimized recursive search
    def _looking(self):
        """Finds supported pictures in dir."""
        for curr_dir, dirs, files in walk(self._dir):
            dirs = sorted(dirs, key=str.lower)
            files = sorted(files, key=str.lower)
            for fileName in files:
                # filter for file extensions, 
                # this must be supported by PIL
                if fileName[-4:].lower() in Kangle.supportedFormats:
                    fullName = join(curr_dir, fileName)
                    if not self.duplicating and self._double(fullName):
                        self.doubleCounter += 1
                        continue
                    self.adjustImage(fullName, self._counter)
                    self._counter += 1
            if not self.deepth:
                break
    
    def _amountFiles(self):
        """Counts amount of supported Files in dir and subdirectories."""
        amount = 0
        for _, _, files in walk(self._dir):
            for fileName in files:
                # filter for file extensions, 
                # this must be supported by PIL
                if fileName[-4:].lower() in Kangle.supportedFormats:
                    amount += 1
            if not self.deepth:
                break
        return amount
  
    def _writeSavePoint(self, targetDir, title, siteno):
        """Writes a resume file for the given title"""
        fileName = glob("%s/pictures/%s/%05d*" % (targetDir, title, siteno))[0]
        with open("%s/pictures/%s.manga_save" % (targetDir, title)) as f:
            f.write("#Fri Sep 02 18:20:13 GMT+01:16 2011")
            f.write("LAST=/mnt/us/pictures/%s/%s" % (title, fileName))
        with open("%s/pictures/%s.manga" % (targetDir, title)) as f:
            f.write("\0")    

    
    def __init__(self, title, targetDir, source, deepth=True, counter=0):
        # eliminate duplicates
        self.duplicating = False
        self._duplicate = {}
        # for statistics
        self.doubleCounter = 0
        # useful when scans have too much white borders
        self.cropping = False
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
        # skipping by damaged images or abort
        self.skipping = True
        self.title = title
        self._targetDir = targetDir
        self._dir = source
        self.deepth = deepth
        # count number of supported Files
        if self.footer:
            self._amount = self._amountFiles()
            self._x = None
        for dir in ["pictures", title]:
            self._targetDir = join(self._targetDir, dir)
            if not isdir(self._targetDir):
                mkdir(self._targetDir)
            elif dir != "pictures":
                print >> stderr, "directory ", dir, " already exists"

if __name__ == "__main__":
    try:
        # sys.argv[2] could look like "D:\"(Windows) or "/media/kindle"(Unix-like)
        title, targetDir = argv[1], argv[2]
    except IndexError:
        if len(argv) > 1 and argv[1] == "--version":
            print "Kangle version ", __version__," by ", __author__
            print "Thanks to", __credits__
            exit(0)
        else:
            print >> stderr, "arguments: TITLE KINDLE_ROOT_DIRECTORY <SOURCE>"
            exit(-1)
    source =  argv[3] if len(argv) > 3 else getcwd()
    kangle = Kangle(title, targetDir, source)
    print "found", kangle._amount, "files"
    print "converting & transferring ...",
    if not kangle.duplicating: 
        print "\ndoubles found: ",
    #cProfile.run('kangle.run()')
    kangle.run()
    if not kangle.duplicating: 
        print "%d" % kangle.doubleCounter
    print "finished"
