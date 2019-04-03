import parseGcode2
def genBinTestData() :
	lines = ('G1 X-4.229 Y19.099 E187.64453', \
			 'G1 X-4.548 Y19.078 E187.70025', \
			 'M190 S50', \
			 'G21        ;metric values', \
			 'G0 F5700 X-7.319 Y-5.812 Z0.42', \
			 'G28', \
			 'G1 F3900 E-5.5', \
			 'G1 X-6.596 Y-6.968 E0.19085', \
			 'G1 F810 X-6.92 Y-6.368 E0.0956', \
			 'G4 S100000', \
  			 'G1 Z-1000', \
  			 'G1 F', \
  			 'M117 Printing....')
	gc = list()
	bgc = list()
	for idx,line in enumerate(lines) :
		gc.append(gcodeCommand())
		gc[idx].parseGcode(line)
		if(idx==1) :
			gc[idx].usePrevFormat = True
		bgc.append(gc[idx].encodeBinGcode())
	return (gc,bgc)

def printBGCdata(bgc) :
	print('{',end='')
	for idx,ch in enumerate(bgc.hex()) :
		if(not idx % 2) :
			print('0x',end='')
		print(ch,end='')
		if(idx %2 and idx<(len(bgc.hex())-1)) :
			print(',',end='')
	print('}',end='')

def printBGC(gc,bgc) :
	print('{')
	print('\t',end='')
	printBGCdata(bgc)
	print(',')
	print('\t'+str(gc.isBinary).lower()+',')
	print('\t'+str(gc.usePrevFormat).lower()+',')
	print("\t'"+gc.cmdPrefix+"',")
	print('\t'+str(gc.cmdCode)+',')
	print('\t'+str(len(gc.par))+',')
	print('\t{',end='')
	for idx,par in enumerate(gc.par) :
		if(idx>0) :
			print('\t',end='')
		printBGCpar(par)
		if(idx<(len(gc.par)-1)) :
			print(',')
		else :
			print('}')
	print('}')

def printBGCpar(bgcpar) :
	print("{'"+bgcpar.parPrefix+"',"+ \
		  str(bgcpar.parVal)+','+ \
		  strBGCparFormat(bgcpar.parFormat)+'}',end='')

def strBGCparFormat(parFormat) :
    strFormat = {
    gcodeParameterFormat.none: 'gcode_NONE',
    gcodeParameterFormat.U8: 'gcode_U8',
    gcodeParameterFormat.U16: 'gcode_U16',
    gcodeParameterFormat.I8:  'gcode_I8',
    gcodeParameterFormat.I16: 'gcode_I16',
    gcodeParameterFormat.I32: 'gcode_I32',
    gcodeParameterFormat.F32: 'gcode_F32',
    gcodeParameterFormat.string: 'gcode_string'
    }[parFormat]
    return strFormat