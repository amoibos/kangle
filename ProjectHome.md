Kangle convert and transfer your manga scans to your kindle device.
It uses the external lib Pillow for image processing and supports compressed archive like cbz, zip, cbr, rar and some tricks for better performance.
Rar support require the external lib Rarfile and the command line tool unrar in your path. Some advanced features like:
  * footer with title and side bar
  * split to wide images
  * stretching to a resolution
  * cropping the white borders
  * numerical sorting
  * finding duplicates
  * look into archives

Quick Start:
Run kangle from the command line with two parameters. The first is the title of the manga and second the root directory of kindle device. Kangle uses your current directory as starting point. Further options are available to overwrite the defaults:
  * change start number, not same as skipping files(--start=0)
  * find duplicates(--duplicating=off|on)
  * stretching(--stretching=on|off)
  * cropping to remove boarders(--cropping=off|on)
  * skipping broken files(--skipping=on|off)
  * numerial sort(--numsort=off|on)
  * splitting too large images(--splitting=on|off)
  * switching source directory(--source=./)
  * depth search(--depth=on|off)
  * resolution(--resolution=600,800)
  * reverse order by a split(--reverse=on|off)

