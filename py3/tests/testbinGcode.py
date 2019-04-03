from binGcode import *
import copy
def encodeGcodeFile(filename="coffee_hanger2D.gcode",filename_out="coffee_hanger2D.bgc") :
    file = open(filename,"r")
    file.seek(0)
    gcode = list()
    prevcmd = None
    for line in file :
        cmd = gcodeCommand()
        isComment = not cmd.parseGcode(line)
        if(not isComment) :
            if(cmd.isEqualFormat(prevcmd)) :
                cmd.usePrevFormat = True
            gcode.append(cmd)
            prevcmd = cmd
    file.close()
    file = open(filename_out,"wb+")
    for cmd in gcode :
        bcmd = cmd.encodeBinGcode()
        file.write(bcmd)
    file.close()

def testBGcodeFile(filename="coffee_hanger2.gcode",filename_out="coffee_hanger2B.bgcode",filename3="coffee_hanger2C.gcode") :
    file2 = open(filename,'r')
    file1 = open(filename_out,'rb')
    file3 = open(filename3,'w')
    gc1 = gcodeCommand()
    gc2 = gcodeCommand()
    prevgc1 = None
    idx = 0
    badgc1 = list()
    badgc2 = list()
    badgcidx = list()
    while(gc1!=None) :
        gc1 = decodeBinGcode(file1,prevgc1)
        prevgc1 = copy.copy(gc1)
        if(gc1==None) :
            break
        isComment = not gc2.parseGcode(file2.readline())
        while(isComment) :
            isComment = not gc2.parseGcode(file2.readline())
        isEqual = gc1.isEqual(gc2)
        if(not isEqual) :
            print("Not equal, i="+str(idx))
            badgc1.append(copy.copy(gc1))
            badgc2.append(copy.copy(gc2))
            badgcidx.append(idx)
        file3.write(gc1.writeGcode('')[0]+'\n')
        idx+=1
    print("ending idx=",str(idx),' ftell=',str(file1.tell()))
    file1.close()
    file2.close()
    file3.close()
    return (badgc1,badgc2,badgcidx)


def readGcodeLine(file) :
    line = file.readline()
    gc2 = gcodeCommand()
    isComment = not gc2.parseGcode(line)
    if(not isComment) :
        print(gc2)
    else :
        print(line)
    return line

def readBinGcodeLine(file,prevcmd=None) :
    print(file.tell())
    gc = decodeBinGcode(file,prevcmd)
    print(gc)
    return gc

def main(argv) :
	filename_in = argv[0]
	filename_out = argv[1]
	encodeBinGcode(filename_in,filename_out)

if __name__ == "__main__":
    main(sys.argv[1:])