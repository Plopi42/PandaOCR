#! /usr/bin/python

import sys
import getopt

try:
   from PIL import Image
except:
   print '''
You are missing the python image librarie (PIL)!
  if you are on a Debian like linux distribution,
    try 'apt-get install python-imaging'
  else
    go to http://www.pythonware.com/products/pil/,
    dowload and install the last version.
'''
   sys.exit(3)

try:
   import cPickle as pickle
except:
   import pickle


class PandaOCR:
  __rColor        = None
  __gColor        = None
  __bColor        = None
  __aColor        = 255
  __treshold      = None

  __cellWidth     = None
  __cellHeight    = None

  __emptyChar     = None

  __pickleFile    = None
  __learnedList   = []

  __percentComp   = True
  __appendTrigger = 950
  __minCoords     = 10
  __cropBorder    = 4

  __debug         = True
  __verify        = False
  __fixedWidth    = True
  __moveCoords    = False


  def __init__(self, hexColor, treshold, cellGeometry, emptyChar,
               pickleFileName = "learned.pickle", percentComp = True,
               debug = True, verify = False, fixedWidth = True,
               moveCoords = False):
    self.dPrint ("Initilazing PandaOCR %x %s %d %s %s" %
      (hexColor, cellGeometry, treshold, emptyChar, pickleFileName))

    self.__setHexColor(hexColor)
    self.__setCellGeometry(cellGeometry)

    self.__treshold  = treshold
    self.__emptyChar = emptyChar

    self.loadPickleFile(pickleFileName)

    self.__percentComp = percentComp
    self.__debug       = debug
    self.__verify      = verify
    self.__fixedWidth  = fixedWidth
    self.__moveCoords  = moveCoords


  def __setHexColor(self, hexColor):
    self.__rColor = (hexColor >> 16) & 0xFF
    self.__gColor = (hexColor >>  8) & 0xFF
    self.__bColor = (hexColor >>  0) & 0xFF


  def __setCellGeometry(self, cellGeometry):
    a = cellGeometry.split("x")
    try:
      self.__cellWidth  = int(a[0])
      self.__cellHeight = int(a[1])
    except:
      self.dPrint ("Incorrect cellGeometry parameter '%s'" % cellGeometry)
      sys.exit(3)


  def loadPickleFile(self, pickleFileName):
    self.__pickleFile = pickleFileName

    try:
      input = open(self.__pickleFile, 'rb')
    except:
      self.dPrint("Unable to open pickle file!")
      return False

    self.__learnedList = []
    try:
      self.__learnedList = pickle.load(input)
    except:
      self.dPrint('Unable to parse pickle file!')
      input.close()
      return False

    input.close()
    return True


  def savePickleFile(self):
    try:
      output = open(self.__pickleFile, 'wb')
    except:
      self.dPrint('Unable to open pickle file!')
      return False

    pickle.dump(self.__learnedList, output)
    output.close()
    return True


  def dPrint(self, msg):
    if self.__debug:
      print msg


  def __check(self, matrix):
    numbers = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]

    for line in matrix:
      for cell in line:
        if (len(cell) != 1):
          return False
        else:
          try:
            i = int(cell[0])
            numbers[i] += 1
          except:
            'Nothing'
    return [ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 ] == numbers


  def __processCellPoints(self, offsetV, offsetH):
    imgWidth, imgHeight = self.__currentImage.size
    maxJ = min(self.__cellHeight, (imgHeight - offsetV))
    maxI = min(self.__cellWidth,  (imgWidth  - offsetH))

    li = []
    out = ''
    for j in range(self.__cropBorder, maxJ):
      outLine = ''
      found = False
      outLine += ("%2.d: " % j)
      for i in range(self.__cropBorder, maxI):
        r, g, b, a = self.__currentImage.getpixel((offsetH + i, offsetV + j))

        diff = max(abs(self.__rColor - r),
                   abs(self.__gColor - g),
                   abs(self.__bColor - b),
                   abs(self.__aColor - a))

        if (diff < self.__treshold):
          outLine += 'X'
          found = True
          li.append((i,j))
        else:
          outLine += '.'

      if found:
        out += outLine + '\n'
    return (self.__moveCoordinates(li), out)


  def __moveCoordinates(self, coordsList):
    if not self.__moveCoords:
      return coordsList

    minX, minY = self.__currentImage.size
    for x, y in coordsList:
      if x < minX:
        minX = x
      if y < minY:
        minY = y

    return map(lambda (x,y): (x - minX, y - minY), coordsList)

  def parseFile(self, fileName, learnB = False):
    try:
       self.__currentImage = Image.open(fileName).convert('RGBA')
    except:
       print '!! Unable to open image file:', fileName
       sys.exit(2)

    imgWidth, imgHeight = self.__currentImage.size

    offsetV = 0
    chars   = []
    matrix  = []
    while ((offsetV + (self.__cellHeight / 2)) <= imgHeight):
      offsetH = 0
      temp    = []
      while ((offsetH + (self.__cellWidth / 2)) <= imgWidth):
        cellCoord, out = self.__processCellPoints(offsetV, offsetH)
        if learnB:
          char, width = self.__learn(cellCoord, out)
        else:
          char, width = self.__processCell(cellCoord, out)

        temp.append(char)
        offsetH += width
      offsetV += self.__cellHeight
      matrix.append(temp)

    self.__currentImage = None
    return matrix


  def __learn(self, cellCoord, out):
    width = self.__cellWidth

    if len(cellCoord) <= self.__minCoords:
      return self.__emptyChar, width

    print out
    print "Which character is printed above ?"
    char  = sys.stdin.readline()[0]

    if not self.__fixedWidth:
      width    = 0
      maxW = min(self.__currentImage.size[0], self.__cellWidth)
      while width == 0:
        try:
          print "What is the width in pixels of the character ? (%d)" % maxW
          tmpWidth = int(sys.stdin.readline())
          if tmpWidth <= maxW:
            width = tmpWidth
        except:
          print "Error: Bad integer"

    temp = (char, cellCoord, width)
    if self.__learnedList.count(temp) == 0:
      self.__learnedList.append(temp)

    return char, width


  def __commonPoints(self, learned, read):
    total = len(learned)
    if total <= self.__minCoords:
      return 0

    common = 0
    for it in learned:
      common += read.count(it)

    if self.__percentComp:
      return (common * 1000) / total
    else:
      return common * 1024


  def __processCell(self, list, out):
    vals = [(self.__emptyChar, self.__cellWidth)]
    if (len(list) <= self.__minCoords):
      return vals[0]

    max = 0
    for val, lst, width in self.__learnedList:
      tmp = self.__commonPoints(lst, list)
      if tmp > max:
        max = tmp
        vals = [(val, width)]
      elif tmp == max:
        vals.append((val, width))

    if ((max < self.__appendTrigger) or len(val) != 1):
      return self.__learn(list, out)

    if max == 0:
      return self.__emptyChar, self.__cellWidth

    return vals[0]


  def display(self, matrice, fileName = "", resultCsv = None):
    if self.__debug:
      print '-- ', fileName
      for line in matrice:
        sys.stdout.write('-- ')
        print line
      print '--'

    outputFd = sys.stdout
    if not (resultCsv is None):
      outputFd = open(resultCsv, 'a')

    outputFd.write('==;' + fileName + ';')
    for line in matrice:
      for col in line:
        outputFd.write(col + ';')
    outputFd.write('\n')
    if not (resultCsv is None):
      outputFd.close()


  def ocrFromFile(self, fileName, resultCsv = None):
    matrix = self.parseFile(fileName, False)

    if self.__verify and (not self.__check(matrix)):
      self.dPrint('!! Error while checking grid for: ' + fileName)
      matrix = self.parseFile(fileName, True)

    self.display(matrix, fileName, resultCsv)
    return matrix



class PandaOCRApp:
  __ocr = None
  __resultCsv = None
  __files = None


  def getOpt(self):
    try:
      opts, args = getopt.getopt(sys.argv[1:],
                                 "hdl:t:c:g:e:nr:vwm",
                                 ["help", "debug", "learned-file=",
                                  "treshold=", "color=", "cell-geometry=",
                                  "empty-char=", "number-mode-comparison",
                                  "result-csv=", "verify", "variable-width",
                                  "move-coordinates"])
    except getopt.GetoptError, err:
      print str(err)
      self.usage(2)

    debug        = False
    pickleFile   = "learned.pickle"
    treshold     = None
    hexColor     = None
    cellGeometry = None
    emptyChar    = None
    percentComp  = True
    verify       = False
    fixedWidth   = True
    moveCoords   = False

    for o, a in opts:
      if o in   ("-h", "--help"):
        self.usage(0)
      elif o in ("-d", "--debug"):
        debug = True
      elif o in ("-l", "--learned-file"):
        pickleFile = a
      elif o in ("-t", "--treshold"):
        try:
          treshold = int(a)
        except:
          self.usage(2, "Bad integer for option --treshold")
      elif o  in ("-c", "--color"):
        try:
          hexColor = int(a, 16)
        except:
          self.usage(2, "Bad integer for option --color")
      elif o in ("-g", "--cell-geometry"):
        cellGeometry = a
      elif o in ("-e", "--empty-char"):
        emptyChar = a[0]
      elif o in ("-n", "--number-mode-comparison"):
        percentComp = False
      elif o in ("--result-csv", "-r"):
        self.__resultCsv = a
      elif o in ("--verify", "-v"):
        verify = True
      elif o in ("--variable-width", "-w"):
        fixedWidth = False
      elif o in ("--move-coordinates", "-m"):
        moveCoords = True
      else:
        self.usage(2, "Unhandled option: '" + o + "'")

    if len(args) == 0:
      self.usage(2, "No files given")

    self.__files = args

    if hexColor is None:
      print "What is the color to look for? (ex: 6b7a8f)"
      try:
        hexColor = int(sys.stdin.readline(), 16)
      except:
        self.usage(2, "Bad integer for color")

    if treshold is None:
      print "What is the threshold to apply on the color? (beetween 0 and 255)"
      try:
        treshold = int(sys.stdin.readline())
      except:
        self.usage(2, "Bad integer for treshold")

    if cellGeometry is None:
      print "What is the geometry of a cell in px? (ex: 30x30)"
      cellGeometry = sys.stdin.readline().rstrip('\n')

    if emptyChar is None:
      print "What is the character used to represent empty cells? (ex: *)"
      emptyChar = sys.stdin.readline()[0]

    if debug:
      print('-! color=(%x)' % hexColor)
      print('-! treshold=' +  str(treshold))
      print('-! cellGeometry=(%s)' % cellGeometry)
      print('-! emptyChar=' + emptyChar)

    self.__ocr = PandaOCR(hexColor, treshold, cellGeometry, emptyChar,
                          pickleFile, percentComp, debug, verify,
                          fixedWidth, moveCoords)


  def usage(self, code, msg = ""):
    print msg
    print '''
Usage: ./PandaOCR.py [OPTIONS] files

OPTIONS:
--------
    -h|--help
        Print this usage and go.

    -d|--debug
        Turn on debug prints.

    -l|--learned-file=<file_name>
        To give/save the program the pre-learned charset.
        If this argument isn't given, the program will default to
        'learned.pickle'.

    -t|--treshold=<number> (from 0 to 255)
        This number will allow to use image where the color of the number
        isn't precise.

    -c|--color=<hex number> (ex: 2e2e2e)
        This is the color the program will look for.

    -g|--cell-geometry=<width>x<height>
        The cell width and height in px.

    -e|--empty-char=<char> (ex: *)
        The character used to represent blank cell.

    -n|--number-mode-comparison
        Turn on a second comparison mode.

    -r|--result-csv=<number>
        The file where the results must be exported, if the argument isn't
        given, the program will default to the standard output.

    -v|--verify
        Will verify if all the number are represented on the analyzed grid.
        If the grid is not correct, the program will learn it.

    -w|--variable-width
        Will allow characters to have variable width

    -m|--move-coordinates
        Will change the coordinates using the up left corner as (0,0)


EXAMPLES:
    Grids:
        ./PandaOCR.py -d *.jpg
        ./PandaOCR.py -d --treshold=30 --color=6b7a8f --cell-geometry=30x30 '--empty-char=*' test/1/*.jpg
        ./PandaOCR.py -d --treshold=50 --color=2e2e2e --cell-geometry=24x23 '--empty-char=*' test/2/*.png
        ./PandaOCR.py -d --treshold=10 --color=ffffff --cell-geometry=36x36 '--empty-char=*' test/3/*.png
        ./PandaOCR.py -d --treshold=40 --color=7d7d7d --cell-geometry=65x69 '--empty-char=*' test/4/*.gif
        ./PandaOCR.py -d --treshold=40 --color=7F7F7F --cell-geometry=58x47 '--empty-char=*' test/6/*.jpg

    Captchas:
        ./PandaOCR.py -d --treshold=40 --color=000000 --cell-geometry=34x59 '--empty-char=*' -w test/5/*.png

    Recommended:
        ./PandaOCR.py -d -r out.csv *.jpg
'''
    sys.exit(code)


  def run(self):
    for file in self.__files:
      self.__ocr.ocrFromFile(file, self.__resultCsv)

    self.__ocr.savePickleFile()
    print "done"


if __name__ == "__main__":
  ocrApp = PandaOCRApp()
  ocrApp.getOpt()
  ocrApp.run()

