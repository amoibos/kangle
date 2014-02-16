#!/usr/bin/env python
#-*- coding: utf-8 -*-

#Copyright 2011, Daniel Oelschlegel <amoibos@gmail.com>
#License: 2-clause BSD

#this program requires a plugged kindle, at least python 2.6 and Pillow(fork of PIL)
#start this program in a subdirectory that contains picture files or
#directories
#press [ALT] + [z] for rereading the entries in pictures on a kindle
#kindle tip: [ALT] + [f] = full screen,  [ALT] + [p] clear the boundary

from __future__ import print_function
from __future__ import division
from PIL import Image, ImageDraw, ImageFilter
from sys import exit, argv, stderr, version_info
from os import walk, mkdir, getcwd
from os.path import join, isdir, getsize, splitext
from glob import glob
from zipfile import ZipFile
from rarfile import RarFile
from getopt import getopt
from re import compile
from threading import Timer
from tempfile import mkdtemp
from shutil import rmtree
from zlib import crc32
#from thread import start_new_thread

## PDF Extraktion
## GUI(TK) 
## Kommandozeilenparameter(Standard abaendern+Parameter info)
## Buildskript und EXE beilegen
## Viewer Testmode

#import cProfile


#getopt or config parser for standalone program behavior
#TODO: BUG image file is truncated (0 bytes not processed)
#       convert('L')

__author__ = "Daniel Oelschlegel"
__copyright__ = "Copyright 2013, %s" % __author__
__credits__ = [""]
__license__ = "BSD"
__version__ = "0.9.0"


if version_info[0] >= 3:
   def unicode(parameter):
       return parameter

#Kangle, a symbiosis of manga and kindle
class Kangle(object):
    """Kangle makes manga scans readable on a kindle device."""
    supported_outputs = ('.jpg', '.png', '.gif', '.bmp')
    compressed_inputs = ('.zip', '.cbz', '.rar', '.cbr')
    
    
    def output_progress(self, percent):
        print("\r%s%%" % percent, end='')
           
    def progress(self, firstRun=False):
        """Call every 30s this function for printing the progress on screen"""
        if self.timerActivated:
            self._thread = Timer(30, self.progress)
            self._thread.start()
            if not firstRun:
                percent = 100 * self._counter // self._number
                if percent not in self._progress:
                    self.output_progress(percent)
                    self._progress[percent] = True
     
    def start(self):
        self.progress(True)
        self.looking(self._dir)
        self._thread.cancel()
        self.output_progress(100)

    #TODO: poly. instead of linear searching(similar to binary search)
    def _cropping(self, image):
        """Crops one color border from scanned image"""
        #bad, needed better filter
        img = image.convert('L').filter(ImageFilter.MaxFilter(size=5))
        width, height = image.size
        #for loops, every side(w,e,n,s : (parameter index, direction))
        direction = (   (2, 1), (0, -1), 
                        (3, 1), (1, -1))
        #regions for checks, start region + end position
        #max 20 percent border cut for each side
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
                
            #for one color pages
            if cnt + 1 >= dim[side]:
                return image
        return image.crop((0+diff[0], 0+diff[2], 
            width-diff[1], height-diff[3]))
    
    #kindle reads the files in order of timestamp
    def adjust_image(self, file_name, counter):
        """Adjusts the image file file_name to kindle screen and use counter for naming."""
        try:
            first = Image.open(file_name)
        except IOError:
            print("damaged image file: %s" % self.file_name, file=stderr)
            if self.skipping:
                return
            exit(-3)
        if self.cropping:
            first = self._cropping(first)
        #resolution of the image
        (width, height) = first.size
        file_name = '%05da%s' % (counter, splitext(file_name)[1])
        #too wide, better splitting in middle
        if width > height and width > self.resolution[0] and self.splitting:
            #take the second half and resize
            second = first.crop((width // 2, 0, width, height))
            first = first.crop((0, 0, width // 2, height))
            #reverse: manga reading style, right to left
            #save in correct order
            if not self.reverse:
                first, second = second, first
            self._save(second, file_name)
            file_name = file_name.replace("a", "b")
        self._save(first, file_name)
        
    def _save(self, image, file_name):
        """Saves the image with the enabled options under the file_name."""
        if self.stretching:
            #for better quality
            try:
                image = image.convert("RGB")
            except IOError:
                #ups, something went wrong
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
        """Sorting algorithm which uses number lexical order"""
        backup = fileList[:]
        try:
            fileList.sort(cmp, key=lambda tFile: float(self.numPattern.search(tFile).group(0)))
        except AttributeError:
            fileList = backup
        return fileList    
        
    #optimized recursive search
    def looking(self, dir):
        """Finds supported pictures in dir."""
        for curr_dir, dirs, files in walk(unicode(dir)):
            dirs = [dir.encode("utf-8").lower() for dir in dirs]
            dirs = self._num_sort(dirs) if self.num_sort else sorted(dirs)
            files = [f.encode("utf-8").lower() for f in files]
            files = self._num_sort(files) if self.num_sort else sorted(files)
            dirs, files = [item.decode("utf-8") for item in dirs],  [item.decode("utf-8") for item in files]
            for file_name in files:
                self.file_name = file_name
                full_name = join(curr_dir, file_name)
                file_extension = splitext(file_name)[1].lower()
                if file_extension in Kangle.compressed_inputs:
                    temp_dir = self._temp_dirs[join(curr_dir, file_name)]
                    self.looking(temp_dir)
                    rmtree(temp_dir)
                elif file_extension in Kangle.supported_outputs:
                    if not self.duplicating and self._double(full_name):
                        self.doubleCounter += 1
                        continue
                    self.adjust_image(full_name, self._counter)
                self._counter += 1
            if not self.deepth:
                break
    
    def _number_files(self, dir, start=0):
        """Counts number of supported Files in dir and subdirectories."""
        number = start
        for base_dir, _, files in walk(unicode(dir)):
            for file_name in files:
                #filter for file extensions, 
                #this must be supported by PIL
                extension = splitext(file_name)[1]
                extension_lower = extension.lower()
                if extension_lower in Kangle.supported_outputs:
                    number += 1
                if extension_lower in Kangle.compressed_inputs:
                    full_path = join(base_dir, file_name.lower())
                    temp_dir = mkdtemp()
                    #TODO: split into threads which are limited to number of cpu  cores
                    ZipFile(full_path).extractall(temp_dir) if extension_lower == ".zip" else RarFile(full_path).extractall(temp_dir)
                    self._temp_dirs[full_path] = temp_dir
                    number = self._number_files(temp_dir, number)
            if not self.deepth:
                break
        return number
  
    def _write_save_point(self, target_dir, title, siteno):
        """Writes a resume file for the given title"""
        file_name = glob("%s/pictures/%s/%05d*" % (target_dir, title, siteno))[0]
        with open("%s/pictures/%s.manga_save" % (target_dir, title)) as f:
            f.write("#Fri Sep 02 18:20:13 GMT+01:16 2011")
            f.write("LAST=/mnt/us/pictures/%s/%s" % (title, file_name))
        with open("%s/pictures/%s.manga" % (target_dir, title)) as f:
            f.write("\0")    

    def __init__(self, title, target_dir, options):
        #eliminate duplicates
        self.duplicating = options["duplicating"]
        self._duplicate, self.doubleCounter  = {}, 0
        #useful when scans have too much white borders
        self.cropping = options["cropping"]
        #reverse order by splitted image, usefull for reading manga
        #comics(left to right), manhwa should use reverse = False
        self.reverse = options["reverse"]
        #splitting if the image is too wide
        self.splitting = options["splitting"]
        #stretching
        self.stretching = options["stretching"]
        #displaying useful footer 
        self.footer = options["footer"]
        #for resuming a session
        self._counter = options["start"]
        #resolution of your kindle, required for stretching
        self.resolution = options["resolution"] 
        #skipping by damaged images or abort
        self.skipping = options["skipping"]
        self.title = title
        self._target_dir = target_dir
        self._dir = options["source"] 
        self.deepth = options["depth"]
        self._buffer = []
        self.timerActivated = True
        #for displaying progress in percent and only once
        self._progress = {} 
        self.num_sort = options["numsort"]
        self._thread = None
        self._temp_dirs = {}
        #count number of supported Files
        if self.footer:
            self.signature = ("%s/%05d@%s", ("splitext(file_name)[0]", 
                "self._number", "self.title"))
            self._number = self._number_files(self._dir)
            self._x = None
        for dir in ["pictures", title]:
            self._target_dir = join(self._target_dir, dir)
            if not isdir(self._target_dir):
                mkdir(self._target_dir)
            elif dir != "pictures":
                print("directory", dir, "already exists", file=stderr)
        self.numPattern = compile(r'\d+')

if __name__ == "__main__":
    options, remainder = getopt(argv[1:], 'aofsrcndtxip:v', [
                                                         'source=',
                                                         'splitting=',
                                                         'cropping=',
                                                         'duplicating=',
                                                         'resolution=',
                                                         'version',
                                                         'footer=',
                                                         'reverse=',
                                                         'numsort=',
                                                         'depth=',
                                                         'stretching=',
                                                         'skipping=',
                                                         'start='
                                                         ])
    additional_options = {"source":getcwd(), "numsort": False, "footer": True,
                            "skipping": True, "depth": True, 
                            "resolution": (600, 800), "start": 0, 
                            "splitting": True, "stretching": True, 
                            "reverse": True, "cropping": False, 
                            "skipping": True, "duplicating": True}
    for opt, arg in options:
        if opt in ('-a', '--start'):
            additional_options["start"] = int(arg)
        elif opt in ('-o', '--source'):
            additional_options["source"] = arg
        elif opt in ('-f', '--footer'):
            additional_options["footer"] = arg.lower() == "on"
        elif opt in ('-s', '--splitting'):
            additional_options["splitting"] = arg.lower() == "on"
        elif opt in ('-r', '--reverse'):
            additional_options["reverse"] = arg.lower() == "on"
        elif opt in ('-c', '--cropping'):
            additional_options["cropping"] = arg.lower() == "on"
        elif opt in ('-n', '--numsort'):
            additional_options["num_sort"] = arg.lower() == "on" 
        elif opt in ('-d', '--duplicating'):
            additional_options["duplicating"] = arg.lower() == "on"     
        elif opt in ('-t', '--depth'):
            additional_options["depth"] = arg.lower() == "on"   
        elif opt in ('-x', '--stretching'):
            additional_options["stretching"] = arg.lower() == "on"  
        elif opt in ('-i', '--resolution'):
            additional_options["resolution"] = map(int, arg.split(",")) 
        elif opt in ('-p', '--skipping'):
            additional_options["skipping"] = arg.lower() == "on"
        elif opt in ('-v', '--version'):
            print("Kangle version", __version__,"by ", __author__)
            print("Thanks to", " ".join(__credits__))
            exit(0)
        
    if len(remainder) == 2:                      
        #target_dir could look like "D:"(Windows) or "/media/kindle"(Unix-like)
        title, target_dir = remainder[0], remainder[1]
    else:
        print("arguments: <OPTIONS> TITLE KINDLE_ROOT_DIRECTORY <SOURCE>", file=stderr)
        for item in additional_options:
            output = additional_options[item]
            if isinstance(additional_options[item], bool):
                output = {True: "on", False: "off"}[additional_options[item]]
            print(item, ": ", output, sep="")
        exit(-1)
    
    kangle = Kangle(title, target_dir, additional_options)
    print("found", kangle._number, "files")
    if kangle._number > 0:
        print("converting & transferring ...")
        if not kangle.duplicating: 
            print("\ndoubles found: ", end="")
        #cProfile.run('kangle.start()')
        kangle.start()
        if not kangle.duplicating: 
            print("%d" % kangle.doubleCounter)
    else:
        print("nothing to do")
