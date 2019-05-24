import struct
from dataclasses import dataclass
from typing import Any
from enum import IntEnum, auto
from functools import reduce
strCMDs = (23,117,28,30,32,33,928)

class gcodeParameterFormat(IntEnum) :
    none = 0  
    U8 = auto()
    U16 = auto()
    I8 = auto()
    I16 = auto()
    I32 = auto()
    F32 = auto()
    string = auto()

@dataclass
class gcodeParameter :
    parPrefix : str = ""
    parVal : Any = None
    parFormat : gcodeParameterFormat = gcodeParameterFormat.none
    def classifyFormat(self) :
        if(self.parVal==None) :
            self.parFormat = gcodeParameterFormat.none
        elif(type(self.parVal)==str) :
            self.parFormat = gcodeParameterFormat.string
        elif(type(self.parVal)==float and not self.parVal.is_integer() ) :
            self.parFormat = gcodeParameterFormat.F32
        else :
            temp = int(self.parVal)
            if(temp>=0) :
                if(temp.bit_length()>16) :
                    self.parFormat = gcodeParameterFormat.I32
                elif(temp.bit_length()>8) :
                    self.parFormat = gcodeParameterFormat.U16
                else :
                    self.parFormat = gcodeParameterFormat.U8
            else :
                if(temp.bit_length()>15) :
                    self.parFormat = gcodeParameterFormat.I32
                elif(temp.bit_length()>7) :
                    self.parFormat = gcodeParameterFormat.I16
                else :
                    self.parFormat = gcodeParameterFormat.I8
    def encodeBinPar(self,usePrevFormat=False) :
        #transform into binary number from 0-25
        # parDesc = self.parPrefix.upper().encode("utf-8") - "A".encode("utf-8")
        # print(parBinFormat)
        if(usePrevFormat) :
            parBinDesc = int(0).to_bytes(0,"little",signed=False)
        else :
            parBinFormat = (int.from_bytes(self.parPrefix.upper().encode("utf-8"),"little",signed=False) - int.from_bytes("A".encode("utf-8"),"little",signed=False)) & ((1<<5)-1)
            parBinDesc = (parBinFormat | int(self.parFormat)<<5).to_bytes(1,"little",signed=False)
        parBinVal = self.to_bytes()
        return parBinDesc + parBinVal
    def to_bytes(self) :
        result = {
            gcodeParameterFormat.none: lambda x: int(0).to_bytes(0,"little",signed=False),
            gcodeParameterFormat.U8: lambda x: int(x).to_bytes(1,"little",signed=False),
            gcodeParameterFormat.U16: lambda x: int(x).to_bytes(2,"little",signed=False),
            gcodeParameterFormat.I8: lambda x: int(x).to_bytes(1,"little",signed=True),
            gcodeParameterFormat.I16: lambda x: int(x).to_bytes(2,"little",signed=True),
            gcodeParameterFormat.I32: lambda x: int(x).to_bytes(4,"little",signed=False),
            gcodeParameterFormat.F32: lambda x: struct.pack("<f",float(x)),
            gcodeParameterFormat.string: lambda x: str(x).encode("utf-8")+b'\x00' #add null character to end
        }[self.parFormat](self.parVal)
        return result
    def from_bytes(self,data) :
        self.parVal = {
            gcodeParameterFormat.none: lambda x: None,
            gcodeParameterFormat.U8: lambda x: int.from_bytes(x.read(1),byteorder='little',signed=False),
            gcodeParameterFormat.U16: lambda x: int.from_bytes(x.read(2),byteorder='little',signed=False),
            gcodeParameterFormat.I8: lambda x: int.from_bytes(x.read(1),byteorder='little',signed=True),
            gcodeParameterFormat.I16: lambda x: int.from_bytes(x.read(2),byteorder='little',signed=True),
            gcodeParameterFormat.I32: lambda x: int.from_bytes(x.read(4),byteorder='little',signed=True),
            gcodeParameterFormat.F32: lambda x: struct.unpack("<f",x.read(4))[0],
            gcodeParameterFormat.string: lambda x: readUntilChar(x,b'\00').decode('utf-8')
        }[self.parFormat](data)
        return self.parVal
    def isEqualFormat(self,par) :
        return self.parPrefix == par.parPrefix and self.parFormat == par.parFormat
    def writeGcode(self,line) :
        startLen = len(line)
        result = {
            gcodeParameterFormat.none: lambda x,y: '%c ' % x,
            gcodeParameterFormat.U8: lambda x,y: '%c%0.0f ' % (x,y),
            gcodeParameterFormat.U16: lambda x,y: '%c%0.0f ' % (x,y),
            gcodeParameterFormat.I8: lambda x,y: '%c%0.0f ' % (x,y),
            gcodeParameterFormat.I16: lambda x,y: '%c%0.0f ' % (x,y),
            gcodeParameterFormat.I32: lambda x,y: '%c%0.0f ' % (x,y),
            gcodeParameterFormat.F32: lambda x,y: '%c%.9g ' % (x,y),
            gcodeParameterFormat.string: lambda x,y: '%c%s ' % (x,y)
        }[self.parFormat](self.parPrefix,self.parVal)
        line+=result
        return (line,len(line)-startLen)
@dataclass
class gcodeCommand :
    isBinary : bool = False
    usePrevFormat : bool = False
    cmdPrefix : str = ""
    cmdCode : int = 0
    par : list = None

    def parseGcode(self, line):
        # line = "G1 X-6.184 Y-8.273 E0.3824\n ;Hello World"
        line = line.partition(";")[0] #remove comments
        line = line.rstrip("\n\r") #remove newline
        if(len(line)==0) :
            return False
        #parse command code
        lineInd = 0
        self.cmdPrefix = line[lineInd] #G or M
        lineInd += 1
        lineEndInd = findNextSpace(line,lineInd)
        self.cmdCode = int(line[lineInd : lineEndInd])
        lineInd += lineEndInd
        self.par = list()
        parInd = 0
        #parse parameters
        while(lineInd<len(line)) :
            nextchar = line[lineInd]
            if(nextchar.isalpha()) :
                par = gcodeParameter()
                par.parPrefix = nextchar #get parameter character code
                lineInd +=1
                lineEndInd = findNextSpace(line,lineInd)
                if(lineEndInd-lineInd>0) :
                    if(not hasAlpha(line[lineInd:lineEndInd])) :
                        par.parVal = float(line[lineInd:lineEndInd])
                        par.classifyFormat()
                    else :
                        par.parVal = line[lineInd:lineEndInd]
                        par.parFormat = gcodeParameterFormat.string
                else :
                    par.parVal = None
                lineInd = lineEndInd + 1
                # print("Par "+str(parInd) + "Prefix " + par.parPrefix + "value " + str(par.parVal))
                self.par.append(par) #Add new parameter
                # print("Par0 "+str(parInd) + "Prefix " + cmd.par[0].parPrefix + "value " + str(cmd.par[0].parVal))
                parInd +=1
            else :
                lineInd += 1
        return True
    def encodeBinGcode(self) : 
        isBinary = True
        isGPrefix = self.cmdPrefix=="G"
        numPar = min(len(self.par),(1<<3)-1)
        if(self.usePrevFormat) :
            cmdBytes = (isGPrefix<<0 | numPar<<1 | self.usePrevFormat<<4 | isBinary<<5                                   ).to_bytes(1,"little",signed=False)
        else :
            cmdBytes = (isGPrefix<<0 | numPar<<1 |                         isBinary<<5 | (self.cmdCode & ((1<<10)-1))<<6 ).to_bytes(2,"little",signed=False)
        parBytes = int(0).to_bytes(0,"little")
        for par in self.par :
            parBytes += par.encodeBinPar(self.usePrevFormat)
        return cmdBytes + parBytes
    


    def isEqualFormat(self,gcode) :
        if(type(gcode) != gcodeCommand) :
            return False
        isEqual = (self.cmdPrefix == gcode.cmdPrefix)
        isEqual &= (self.cmdCode == gcode.cmdCode)
        isEqual &= len(self.par) == len(gcode.par)
        parIdx = 0
        for idx,par in enumerate(self.par) :
            if(isEqual) :
                isEqual &= par.isEqualFormat(gcode.par[idx])
            else :
                break
            parIdx+=1
        return isEqual
    def isEqual(self,gcode) :
        isEqual = self.isEqualFormat(gcode)
        for idx,par in enumerate(self.par) :
            if(not isEqual) :
                break
            if(par.parFormat==gcodeParameterFormat.none) :
                pass
            elif(par.parFormat==gcodeParameterFormat.string) :
                isEqual &= par.parVal == gcode.par[idx].parVal
            else :
                isEqual &= abs(par.parVal-gcode.par[idx].parVal) <0.01
        return isEqual
    def writeGcode(self,line) :
        startLen = len(line)
        line += ('%c%d ' % (self.cmdPrefix,self.cmdCode))
        for par in self.par :
            (line,count) = par.writeGcode(line)
        # line+='\r\n'
        return (line,len(line)-startLen)




def decodeBinPar(data) :
    parBytes = data.read(1)[0]
    parFormat = gcodeParameterFormat(parBytes>>5)
    parPrefix = parBytes & ((1<<5)-1)
    parPrefix = ((parPrefix + b'A'[0]).to_bytes(1,'little',signed=False)).decode('utf-8') #add binary value to 'A' to get the character code
    par = gcodeParameter()
    par.parPrefix = parPrefix
    par.parFormat = parFormat
    par.from_bytes(data)
    return par

#Decode incoming data stream for next Parameter command.  It's assumed that the first byte is the command code.  This also assumes that this is not previous command format
def decodeBinGcode(data,prevcmd=None) :
    cmdBytes = data.read(1)
    if(len(cmdBytes)==0) :
        return None
    else :
        cmdBytes = cmdBytes[0]
    isBinary = cmdBytes>5
    usePrevFormat = (cmdBytes & (1<<4)) >> 4
    numPar = cmdBytes>>1 & ((1<<3)-1)
    if(not isBinary or (usePrevFormat and prevcmd==None)) :
        return None
        # pass
    if(not usePrevFormat) :
        cmdPrefix = "G" if (cmdBytes & 0x01) else "M" 
        cmdBytes = cmdBytes.to_bytes(1,'little')+data.read(1)
        cmdCode = int.from_bytes(cmdBytes,byteorder='little',signed=False) >> 6
    else:
        cmdPrefix = prevcmd.cmdPrefix
        cmdCode = prevcmd.cmdCode
        par = prevcmd.par
    cmd = gcodeCommand()
    cmd.isBinary = isBinary
    cmd.usePrevFormat = usePrevFormat
    cmd.cmdPrefix = cmdPrefix
    cmd.cmdCode = cmdCode
    cmd.par = par if usePrevFormat else list()
    if(not usePrevFormat) :
        for i in range(0,numPar) :
            cmd.par.append(decodeBinPar(data))
    else:
        for i in range(0,numPar) :
            # data.read(1) #read 0x00 header byte
            cmd.par[i].from_bytes(data)
    return cmd
                
def readUntilChar(data,endchar) :
     ch = data.read(1)
     out = bytearray(ch)
     while(ch!=endchar) :
         ch = data.read(1)
         out.extend(ch)
     return out[0:-1]


        
def hasAlpha(par) :
    for char in par :
        if(char.isalpha()) :
            return True
    return False

def findNextSpace(line,lineInd) :
    lineEndInd = line.find(" ",lineInd)
    if(lineEndInd == -1) : 
        lineEndInd = len(line)
    return lineEndInd
