import serial
import time
import sys
import os
from math import floor

class progFileHandler() :
	def __init__(self,filename) :
		self.filename = filename
		self.file = open(filename,'w')
	def updateProgFile(self,percent) :
		try :
			if(percent<1.0) :
				self.file.seek(0)
				self.file.write('%03d' % int(percent*100))
				self.file.flush()
			elif(os.path.exists(self.filename)) :
				self.file.seek(0)				
				self.file.write('%03d' % int(100))
				self.file.flush()				
				self.file.close()
				os.remove(self.filename)
		except :
			pass

class fakeSerial() :
	def __init__(self) :
		self.inputPath = 'infile.txt'
		self.outputPath = 'outfile.txt'
		self.inputFile = open(self.inputPath,'r')
		self.outputFile = open(self.outputPath,'w')
		self._in_waiting = 0
	def write(self,stream) :
		self.outputFile.write(stream.decode())
	def read(self,stream) :
		return self.inputFile.read(stream).encode()
	def readline(self) :
		return self.inputFile.readline().encode()
	@property
	def in_waiting(self):
		pos = self.inputFile.tell()
		numbytes = self.inputFile.readline()
		self.inputFile.seek(pos)
		return len(numbytes)
	def close(self) :
		self.inputFile.close()
		self.outputFile.close()

def M34_sendBinGcode(ser_obj_in,baudrate,filename,comport='',linetimeout=0.010,linetimeoutmod=1,chunksize=512,progHandle=None) :
	# if(not ser_obj.isOpen()) :
		# ser_obj = serial.Serial(COMPORT,BAUDRATE,timeout=10000,writeTimeout=10000,parity=serial.PARITY_NONE)
	# filename = "coffee_hanger2.gcode"
	# filename = "80hexagon_1p2.gcode"
	# filename = 'coffee_hanger2D.bgc'
	# filename_out = "coffee2.bgc"
	if(ser_obj_in==None) :
		ser_obj = serial.Serial(comport,baudrate,timeout=10000,writeTimeout=10000,parity=serial.PARITY_NONE)
	else :
		ser_obj = ser_obj_in
	file = open(filename,"r+b")
	t = time.time()
	print("Starting")
	print(t)
	print('{:s}'.format(ser_obj.read(ser_obj.in_waiting).decode()))
	#M34filename = filename if(isDosName(filename)) else dosify(filename)
	M34filename = filename
	filesize = os.path.getsize(M34filename)
	ser_obj.write("M34 S{} !{}\n".format(filesize,os.path.split(M34filename)[1]).encode())
	#ser_obj.write(("M34 "+os.path.split(M34filename)[1]+"\r\n").encode())
	ok = ser_obj.readline().rstrip()
	while(ok != 'ok'.encode()) :
		print(ok.decode())
		if(ok.find('failed'.encode()) != -1) :
			print('SD error, quitting')
			return
		ok = ser_obj.readline().rstrip()
		print(time.time() - t)
		if((time.time() - t) >10) :
			print('Did not receive OK')
			return
	print(ok.decode())			
	ok = ser_obj.read(ser_obj.in_waiting)
	print(ok.decode())
	i = 0
	bytesread = file.read(chunksize)
	cts = True
	busySTR = 'busy'.encode()
	okSTR = 'ok'.encode()
	prog = 0
	newprog = 0
	while(bytesread or not cts) :
		if(progHandle) :	
			newprog = newprog + len(bytesread)/filesize
			if(newprog-prog>0.01) :
				prog = newprog
				progHandle(prog)
		if(cts and ser_obj.in_waiting>=len(busySTR)) :
			temp = ser_obj.readline()
			print(temp)
			if(temp.find(busySTR)!=-1) :
				cts = False
				print('i={} waiting for ok\n'.format(i))
		elif(not cts and ser_obj.in_waiting>=len(okSTR)) :
			temp = ser_obj.readline()
			print(temp)
			if(temp.find(okSTR)!=-1) :
				cts = True
				print('i={} ok received, continuing transfer\n'.format(i))
		if(cts) :
			ser_obj.write(bytesread)
			bytesread = file.read(chunksize)	
			if(i%linetimeoutmod==0) :
				time.sleep(0.010) if(i*chunksize<8000) else time.sleep(linetimeout)
			i+=1
	if(progHandle) :	
			progHandle(1.0)			
	t2 = time.time() -t
	time.sleep(2.0)
	ser_obj.write("M29\r\n".encode())
	time.sleep(0.75)
	print(ser_obj.read(ser_obj.in_waiting).decode())
	print(t2)
	c = file.tell()
	print("numbytes = %d" % (c))
	print("Data rate = %f" % (float(c)/t2))
	file.close()
	if(ser_obj_in==None) :
		ser_obj.close()
def isDosName(filename) :
	filesplit = os.path.split(filename)[1].split('.')
	return len(filesplit[0])<=8 and len(filesplit[1]) <=3

def dosify(filename) : 
	return os.path.split(filename)[1].split(".")[0][:8] + ".bgc"
def main(argv) :
	COMPORT = argv[0]
	BAUDRATE = argv[1]
	FILENAME = argv[2]
	if(len(argv)>3) :
		PROGNAME = argv[3]
		progHandler = progFileHandler(PROGNAME)
		PROGHANDLE = progHandler.updateProgFile
	else :
		PROGHANDLE = None
	ser_obj = serial.Serial(COMPORT,BAUDRATE,timeout=10000,writeTimeout=10000,parity=serial.PARITY_NONE)
	# ser_obj = fakeSerial()
	M34_sendBinGcode(ser_obj,BAUDRATE,FILENAME,linetimeout=0.00,progHandle=PROGHANDLE)
	ser_obj.close()
if __name__ == "__main__":
    main(sys.argv[1:])

