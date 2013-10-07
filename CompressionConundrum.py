from PIL import Image, ImageFont, ImageDraw
from cStringIO import StringIO
import os
import copy
import multiprocessing
import time
import sys

class CompressionConundrum():
	def __init__(self):
		pass
		
	def loadImage(self, path):
		image = Image.open(path)
		
		return image
		
	def fitImages(self, imageOne, imageTwo):
		newWidth = min(imageOne.size[0], imageTwo.size[0])
		newHeight = min(imageOne.size[1], imageTwo.size[1])
		
		return imageOne.resize((newWidth,newHeight),Image.ANTIALIAS), imageTwo.resize((newWidth,newHeight),Image.ANTIALIAS)
				
	def getImageDifferencePercentage(self, imageOne, imageTwo, fit=False):
		# Determine the percentage of difference between two images by comparing each
		# of their respective pixels. Requires two images of the exact same size.
		# Will allow the images to be fit unto each other.
		
		if imageOne.size != imageTwo.size and not fit:
			raise ArgumentError, "The images should be the same size."
			
		elif imageOne.size != imageTwo.size and fit:
			imageOne,imageTwo = self.fitImages(imageOne, imageTwo)
			
		imOne = imageOne.load()
		imTwo = imageTwo.load()
		
		differences = []
		
		print imageOne.size, imageTwo.size
		
		for y in range(imageOne.size[0]):
			for x in range(imageOne.size[1]):
				# Coordinates are x and y
				try:
					diff = self.getPixelDifferencePercentage( imOne[x,y], imTwo[x,y] )
				except:
					return float(sum(differences))/len(differences) if len(differences) > 0 else 0
				differences.append(diff)
				
		return float(sum(differences))/len(differences) if len(differences) > 0 else 0
				
		
	def getPixelDifferencePercentage(self, rgbOne, rgbTwo):
		# Determines the difference in color between two pixels by taking
		# their respective RGB values, comparing them and finding the percentage of 
		# difference in each channel, then taking the mean of these percentages
		depth = 255
		r,g,b = [float(abs(one-two))/depth * 100 for one,two in zip(rgbOne, rgbTwo)]
		return sum((r,g,b))/3
		
	def getFileSize(self, file):
		file.seek(0,os.SEEK_END)
		return file.tell()
	

class CCSettings():
	# Class to store test settings
	def __init__(self, width=None, height=None, scale=1, format="JPEG", quality=100):
		self.width = width
		self.height = height
		self.scale = scale
		self.format = format
		self.quality = quality
		
	def setScale(self, scale):
		if self.width and self.height:
			self.width = int(self.width * scale)
			self.height = int(self.height * scale)
			self.scale = scale
		return self
	
	def __int__(self):
		return
	
# Sample image run
def runFolder(cc, folder):	
	samples = os.listdir(folder)
	s = 0
	while s < len(samples):
		if samples[s].split(".")[-1] not in ["jpg","jpeg","png","tiff"]:
			print "Unknown extension for '%s', skipping." % samples[s]
			s+=1
		elif len(multiprocessing.active_children()) < multiprocessing.cpu_count()-1:
			print "Starting new Process."
			p = multiprocessing.Process(target=createImageOverview, args=(cc,samples[s]))
			p.start()
			s+=1
		
		time.sleep(1)
		
		
def createImageOverview(cc, image):
	font = ImageFont.truetype("Arial.ttf", 15)
	ok = Image.open("ok.png","r")
	cancel = Image.open("cancel.png","r")
	up = Image.open("up.png","r")
	down = Image.open("down.png","r")
	
	path = os.path.abspath( os.path.join("samples", image) )
	original = cc.loadImage( path )
	originalSize = os.path.getsize(path)
	
	print "Loading", path
	
	testSettings = []
	
	for q in range(1,101,5):
		testSettings.append( CCSettings(	width=original.size[0], 
											height=original.size[1],
											format="JPEG",
											scale=1,
											quality=q	) )
	
	# Allow for different sizes
	nTestSettings = []		
	for t in testSettings:
		nTestSettings.append((	#copy.deepcopy(t).setScale(3), 
								#copy.deepcopy(t).setScale(2), 
								#copy.deepcopy(t).setScale(1.5),			
								t,
								copy.deepcopy(t).setScale(0.66),
								copy.deepcopy(t).setScale(0.5),
								copy.deepcopy(t).setScale(0.33),
								copy.deepcopy(t).setScale(0.25)))
	
	smallest = min( [t.scale for t in nTestSettings[0]] )
	
	# Create the canvas to display the results
	
	iw = int( original.size[0]*smallest )
	ih = int( original.size[1]*smallest )
	
	w = int( original.size[0]*smallest * len(nTestSettings[0]) )
	h = int( ih * len(nTestSettings) )
	
	canvas = Image.new( "RGB", (w,h), "white" )
	
	cx, cy = 0,0			
	
	nTestSettings.reverse()
	for t in nTestSettings:
		for s in t:
			buffer = StringIO()
			scaled = copy.copy(original)
			scaled = scaled.resize((s.width,s.height))
			scaled.save(buffer, s.format, quality=s.quality)
			fileSize = cc.getFileSize(buffer)
			
			buffer.seek(0)
			
			scaledIm = Image.open(buffer, "r")
			difference = cc.getImageDifferencePercentage(original, scaledIm, fit=True)
			scaledIm = scaledIm.resize((iw,ih), Image.ANTIALIAS)
			scaledDraw = ImageDraw.Draw(scaledIm)
			
			totalPixels = s.width * s.height
			resizedPixels = iw * ih
			ratio = float(resizedPixels)/float(totalPixels)
			
			d = difference*10*ratio
			
			if d < 4:
				scaledIm.paste( ok, (iw-48, 0), mask=ok)
			else:
				scaledIm.paste( cancel, (iw-48, 0), mask=cancel)
				
			if fileSize > originalSize:
				scaledIm.paste( up, (iw-96, 0), mask=up)
			else:
				scaledIm.paste( down, (iw-96, 0), mask=down)
				
			
			# Draw text with shadow
			text = "%sx%s R:%s Q:%s S:%skb D:%.2f%% V:%.2f" % (s.width, s.height, ratio, s.quality, fileSize/1024, d , d / (fileSize/1024))
			print text
			scaledDraw.text( (6,6), text, (0,0,0), font=font)
			scaledDraw.text( (5,5), text, (255,255,255), font=font )
			
			
			bytesPerPixel = (s.width*s.height)/fileSize				
			# paste the image on the canvas				
			canvas.paste(scaledIm, (cx, cy))
			
			cx += iw
			
		cx = 0
		cy += ih
		
		canvas.save(image+"_overview.png")
		
if __name__ == "__main__":
	cc = CompressionConundrum()
	if "demo" in sys.argv[1:]:
		runFolder(cc, "samples")
	elif len(sys.argv) > 1:
		path = sys.argv[1]
		if not os.path.exists(path):
			print "This file could not be found."
			sys.exit()
		
		if os.path.isfile(path):
			createImageOverview(cc, path )
		elif os.path.isdir(path):
			runFolder(cc,path)
	else:
		print "Welcome to CompressionConundrum."
		print "Run this program with 'demo' as an argument to start plowing through the images in the 'samples' folder."
		print "Run this program with a filename as an argument to generate an overview for that image."
		print "Run this program with a folder as an argument to generate an overview for all the images in that folder."
	
