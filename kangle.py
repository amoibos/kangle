#! /usr/bin/env python

#Copyright 2011 Daniel Oelschlegel. All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are
#permitted provided that the following conditions are met:
#
#   1. Redistributions of source code must retain the above copyright notice, this list of
#      conditions and the following disclaimer.
#
#   2. Redistributions in binary form must reproduce the above copyright notice, this list
#      of conditions and the following disclaimer in the documentation and/or other materials
#      provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ``AS IS'' AND ANY EXPRESS OR IMPLIED
#WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> OR
#CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#The views and conclusions contained in the software and documentation are those of the
#authors and should not be interpreted as representing official policies, either expressed
#or implied, of Daniel Oelschlegel.


# this program requires a plugged kindle, at least python 2.* and PIL
# start this program in a subdirectory that contains picture files or directories
# press [ALT] + [z] for rereading the entries in pictures on a kindle

import sys
import os
import Image

# version tracker
version = 0.1
author = "Daniel Oelschlegel"
# global variable counter needed for recursive search
counter = 0
# resolution of your kindle, required for stretching and splitting
width = 600
height = 800
screen = (width, height)
# target_dir is the kindle root directory, dummy value
target_dir = 'D:\\'

# kindle reads the files in order of timestamp
def adjustImage((filename, counter)):
	st = Image.open(filename)
	# prevents IOError with this type
	if st.mode == 'P':
		special = True
	else:
		special = False	
	# resolution of the image, width and height
	(w, h) = st.size
	filename = str(counter).rjust(6, '0') + 'a.jpg'
	# too wide, better splitting in middle and stretching
	if w > h:
		# take the second half and resize
		nd = st.crop((w / 2, 0, w, h)).resize(screen)
		st = st.crop((0, 0, w / 2, h))
		second = os.path.join(target_dir, filename)
		# manga reading style, right to left, save in correct order
		if not special:
			nd.save(second, "JPEG")
		else:
			nd.convert("RGB").save(second, "JPEG")
		filename = filename.replace('a.jpg', 'b.jpg')
	st = st.resize(screen)
	first = os.path.join(target_dir, filename)
	if not special:
		st.save(first, "JPEG")
	else:
		st.convert("RGB").save(first, "JPEG")

# recursive searching
def looking(dir_name):
	dirs = []
	files = []
	for item in os.listdir(dir_name):
		item = os.path.join(dir_name, item)
		if os.path.isfile(item):
			files.append(item)
		else:
			dirs.append(item)
	if files:
		tasks = []
		# some OSes need this, additional sorting
		files.sort()
		for filename in files:
			global counter
			name = filename[-4:].lower()
			# filter for file extensions, 
			# this must be supported by PIL
			if name =='.jpg' or \
				name == '.png' or \
				name == '.gif':
				tasks.append((filename, counter))
				counter += 1
		map(adjustImage, tasks)
	
	# continue with subdirectories
	for dir in dirs:
		looking(dir)

def main():
	global target_dir
	
	if len(sys.argv) < 2:
		print "arguments: <TITLE> <KINDLE_ROOT_DIRECTORY>"
		sys.exit(-1)
	if sys.argv[1] == "--version":
		print "Kangle version " + version + " by " + author
		sys.exit(0)
	
	# sys.argv[2] could look like "D:\"(windows) or "/media/kindle"(unix-like)
	target_dir = sys.argv[2]
	for dir in ["pictures", sys.argv[1]]:
		target_dir = os.path.join(target_dir, dir)
		if not os.path.isdir(target_dir):
			print "creating directory " + target_dir
			os.mkdir(target_dir)
		elif dir == sys.argv[1]:
			print "directory " + dir + " already exists"
	print "converting & transferring ...",
	looking(os.getcwd())
	print "finished"

if __name__ == "__main__":
	main()
	