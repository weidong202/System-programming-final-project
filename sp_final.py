# 逐格掃描
Mnemonic = {'ADD': '18','ADDF': '58','ADDR': '90','AND': '40','CLEAR': 'B4','COMP': '28',
'COMPF': '88','COMPR': 'A0','DIV': '24','DIVF': '9C','FIX': 'C4','FLOAT': 'C0','HIO': 'F4',
'J': '3C','JEQ': '30','JGT': '34','JLT': '38','JSUB': '48','LDA': '00','LDB': '68','LDCH': '50',
'LDF': '70','LDL': '08','LDS': '6C','LDT': '74','LDX': '04','LPS': 'D0','MULF': '60','MULR': '98',
'NORM': 'C8','OR': '44','RD': 'D8','RMO': 'AC','RSUB': '4C','SHIFTL': 'A4','SHIFTR': 'A8','SIO': 'F0',
'SSK': 'EC','STA': '0C','STB': '78','STCH': '54','STF': '80','STI': 'D4','STL': '14','STS': '7C',
'STSW': 'E8','STT': '84','STX': '10','SUB': '1C','SUBF': '5C','SUBR': '94','SVC': 'B0','TD': 'E0',
'TIO': 'F8','TIX': '2C','TIXR': 'B8','WD': 'DC'}
MFormat = {'ADD': 3,'ADDF': 3,'ADDR': 2,'AND': 3,'CLEAR': 2,'COMP': 3,
'COMPF': 3,'COMPR': 2,'DIV': 3,'DIVF': 3,'FIX': 1,'FLOAT': 1,'HIO': 1,
'J': 3, 'JEQ': 3,'JGT': 3,'JLT': 3,'JSUB': 3,'LDA': 3,'LDB': 3,'LDCH': 3,
'LDF': 3,'LDL': 3,'LDS': 3,'LDT': 3,'LDX': 3,'LPS': 3,'MULF': 3,'MULR': 2,
'NORM': 1,'OR': 3,'RD': 3,'RMO': 2,'RSUB': 3,'SHIFTL': 2,'SHIFTR': 2,'SIO': 1,
'SSK': 3,'STA': 3,'STB': 3,'STCH': 3,'STF': 3,'STI': 3,'STL': 3,'STS': 3,
'STSW': 3,'STT': 3,'STX': 3,'SUB': 3,'SUBF': 3,'SUBR': 2,'SVC': 2,'TD': 3,
'TIO': 1,'TIX': 3,'TIXR': 2,'WD': 3}
# DIVR MUL
# SVC not for register
# SHIFT r1,n

register = {"A":"0", "X":"1", "L":"2", "B":"3", "S":"4", "T":"5", "F":"6", "PC":"8", "SW":"9"}

# i = 1 後面接數字不用 M
# i = 1 後面不是數字要 M
# e = 1 都要

def output(loc, objectCode, row, outputStr, change=0):
    # print(f'{loc:X}',objectCode)
    # change == 1 
    if change == 1:
        # clear row and print row
        if row:
            outputStr[0]+= 'T '+f'{row[0]:0>6X} '+f'{row[1]//2:0>2X} '+' '.join(row[2])+'\n'
            row.clear()
        outputStr[0]+= 'T '+f'{loc:0>6X}'+' 02 '+objectCode+'\n'
        return
    # empty list
    if row and row[1] + len(objectCode) >= 60:
        outputStr[0]+= 'T '+f'{row[0]:0>6X} '+f'{row[1]//2:0>2X} '+' '.join(row[2])+'\n'
        row.clear()
    if not row:
        # loc append to row
        # append another list to row
        row.append(loc)
        row.append(0)
        row.append([])
        
    row[2].append(objectCode)
    row[1] += len(objectCode)
    # put the objectCode to the list in row
    # row better form [startAddress,[objectProgram]]


def refill(loc,label,symnode, symtab, base, row, outputStr):
    # label contain nixbpe
    for i in symnode[label]:
        operand = addrCalculate(i[0],loc,i[1],symtab,base,1)
        if operand == '-1':
            print(i[2],'Base referenced before assignment')

        output(i[0]+1,transNIXBPE(0,i[1],operand), row, outputStr, 1)
    del(symnode[label])

def addrCalculate(loc,ta,nixbpe,symtab, base, _refill = 0):
    disp = 0
    try:
        if nixbpe[5 if _refill == 0 else 3] == 1:
            # operand = f'{disp:X}'
            # operand = ta ?
            # 直接定址
            operand = f'{ta:0>3X}'
            pass
        elif ta - (loc + 3) > -2048 and ta - (loc + 3) < 2047: 
            nixbpe[4 if _refill == 0 else 2] = 1
            if ta - (loc + 3) < 0:
                disp = ta - (loc + 3) + 4096
            else:
                disp = ta - (loc + 3)
            operand = f'{disp:0>3X}'
        # TODO check symtab[base] if not exist append to symnode maybe
        elif ta - symtab[base] < 4095:
            nixbpe[3 if _refill == 0 else 1] = 1
            disp = ta - symtab[base]
            operand = f'{disp:0>3X}'
        else:
            # disp out of range
            print('error')
    except KeyError:
        return '-1'
    return operand

def transNIXBPE(m,nixbpe,o=''):
    if m != 0:
        m = int(m,16)
        return f'{m+nixbpe[0]*2+nixbpe[1]:0>2X}'+f'{nixbpe[2]*8+nixbpe[3]*4+nixbpe[4]*2+nixbpe[5]:X}'+o
    else:
        if nixbpe[3] == 1:
            return o
        else:
            return f'{nixbpe[0]*8+nixbpe[1]*4+nixbpe[2]*2+nixbpe[3]:X}'+o

def charset(f):
    start = False
    end = False
    header = []
    symtab = {}
    symnode = {}
    loc = 0
    base = False
    base_name = ''
    first = ''
    row = []
    rows = 0
    outputStr = ['']
    errorFlag = False
    modif = []
    for line in f:
        # nixbpe
        inst = []
        # Register AXLBSTF PC SW
        # n = 1 @ 間接定址
        # i = 1 # 直接定址
        # e = 1 + 4byte
        nixbpe = [0,0,0,0,0,0]
        char = ''
        for c in line:
            if c == '.':
                if char.strip() != '':
                    inst.append(char)
                rows += 1
                break
            if c == ' ' or c == '\t' or c == ',':
                if char.strip() != '':
                    inst.append(char)
                if c == ',':
                    nixbpe[2] = 1
                char = ''
                # continue
            elif c == '+':
                nixbpe[5] = 1
            elif c == '@':
                nixbpe[0] = 1
            elif c == '#':
                nixbpe[1] = 1
            # 換行
            elif c == '\n' :
                if char:
                    inst.append(char)
                    if nixbpe[0] == 0 and nixbpe[1] == 0:
                        nixbpe[0] = 1
                        nixbpe[1] = 1
                rows += 1
                break
            else:
                char+=c

        # empty list
        if not inst:
            continue

        if 'START' in inst:
            if start == False:
                start = True
                inst.remove('START')
                header = inst
                loc = int(inst[1],16)
                symtab[inst[0]] = int(inst[1],16)
                # start label need to append to symtab
                continue
            else:
                # TODO duplicate start error
                print(rows,'duplicate start')
                errorFlag = True
        elif start == False:
            print(rows,'missing START')
            errorFlag = True
            start = True
            header = ['TEST','0']
            loc = 0
        if 'END' in inst:
            outputStr[0] += 'T '+f'{row[0]:0>6X} '+f'{row[1]//2:0>2X} '+' '.join(row[2])+'\n'
            first = inst[1]
            # TODO error detection
            end = True
            continue
        elif end == True:
            print(rows,'The instruction under END will not being process')
            errorFlag = True

        if inst[0] == 'RSUB':
            loc += 3
            output(loc,transNIXBPE(Mnemonic[inst[0]],nixbpe,'000'),row, outputStr)
            continue

        if inst[1] == 'RESW' or inst[1] == 'RESB':
            if inst[0] not in symtab:
                symtab[inst[0]] = loc
                if inst[0] in symnode:
                    refill(loc, inst[0], symnode, symtab, base_name, row, outputStr)
                if inst[1] == 'RESW':
                    loc += int(inst[2]) * 3
                else:
                    loc += int(inst[2])
            else:
                # duplicate symbol error
                print(rows,'duplicate symbol declare:', inst[0])
                errorFlag = True

        elif inst[1] == 'WORD' or inst[1] == 'BYTE':
            if inst[0] not in symtab:
                symtab[inst[0]] = loc
                if inst[0] in symnode:
                    refill(loc, inst[0], symnode, symtab, base_name, row, outputStr)

                if inst[1] == 'WORD':
                    # print('WORD',inst[2])
                    output(loc, inst[2], row, outputStr)
                    loc += 3
                    # TODO check WORD limit
                else:
                    # C
                    if inst[2][0] == 'C':
                        tmp = ''
                        for i in [f'{ord(i):x}' for i in inst[2][2:-1]]:
                            tmp+=i
                        output(loc,tmp,row, outputStr)
                        loc += len(inst[2]) - 3
                    # X
                    elif inst[2][0] == 'X':
                        # TODO format error
                        output(loc, inst[2][2:-1], row, outputStr)
                        loc += 1
                        pass
                    else:
                        # TODO finish this
                        print(rows, ' BYTE format error:',*inst)
                        
                    # TODO 要想一下要不要設大小
            else:
                # duplicate symbol error
                print(rows,'duplicate symbol declare:', inst[0])
                errorFlag = True              

        elif inst[0] in Mnemonic or inst[1] in Mnemonic:
            if inst[1] in Mnemonic:
                # label remove
                if inst[0] not in symtab:
                    symtab[inst[0]] = loc
                    if inst[0] in symnode:
                        refill(loc,inst[0],symnode, symtab, base_name, row, outputStr)
                    inst.remove(inst[0])
                else:
                    print(rows,'duplicate symbol declare:', inst[0])
                    errorFlag = True
                    continue

            # Mnemonic[inst[0]]
            # n = 1 @ 間接定址
            # i = 1 # 直接定址
            # e = 1 + 4byte
            instFormat = MFormat[inst[0]]

            
            if instFormat == 1:
                loc += 1
                output(loc, Mnemonic[inst[0]], row, outputStr)
                continue
            elif instFormat == 2:
                # x == 0
                if nixbpe[2] == 0:
                    output(loc, Mnemonic[inst[0]]+register[inst[1]]+"0", row, outputStr)
                # x ==1
                else:
                    output(loc, Mnemonic[inst[0]]+register[inst[1]]+register[inst[2]], row, outputStr)
                loc += 2
                continue
            elif instFormat == 3:

                if inst[0] == 'LDB':
                    base = True

                operand = ''
                if inst[1].isdigit():
                    # TODO check limit and format
                    if nixbpe[5] == 1:
                        operand = f'{int(inst[1]):0>5X}'
                    else:
                        operand = f'{int(inst[1]):0>3X}'
                elif inst[1] not in symtab:
                    operand = '000'
                    if nixbpe[5] == 1:
                        operand = '00000'
                        modif.append(loc)

                    if inst[1] not in symnode.keys():
                        symnode[inst[1]] = [[loc,nixbpe[2:],rows]]
                    else:
                        symnode[inst[1]].append([loc,nixbpe[2:],rows])
                else:
                    # p+-2048
                    # b+4095
                    # bp是填入時檢查
                    # 先檢查距離再決定 bp
                    if nixbpe[5] == 1:
                        modif.append(loc)

                    ta = int(symtab[inst[1]])
                    operand = addrCalculate(loc,ta,nixbpe,symtab,base_name)
                    if operand == '-1':
                        print(rows, 'Base referenced before assignment')

                # 16 進位字串轉 int 
                # f'{tmp:x}' 轉 16 進位
                # nixbep 應該只用來輸出 不用做其他事情
                #        ni xbpe
                # 0000 0000 0000 0000 0000 0000
                output(loc, transNIXBPE(Mnemonic[inst[0]],nixbpe)+operand, row, outputStr)

            if nixbpe[5] == 0:
                loc+=3
            else:
                loc+=4

        elif inst[0] == 'BASE':
            if base == False:
                print(rows,'error base not found')
            else:
                base = False
                base_name = inst[1]
            continue
        else:
            # TODO no matching error
            print(rows,'no matching mnemonic:',inst[0] if len(inst) < 3 and nixbpe[2] == 0 else inst[1] )
            
    if symnode:
        errorFlag = True
        for i in symnode:
            print(f'Undefined Symbol {i} at {symnode[i][0][2]}')

    # errorFlag = True

    for i in modif:
        outputStr[0] += f'M {i+1:0>6X} 05\n'

    if errorFlag == False:
        with open('107213024王為棟_output.txt','w+') as f:
            f.write('H '+f'{header[0]:>6} '+f'{header[1]:0>6}' +f' {loc-int(header[1],16):X}\n')
            f.write(outputStr[0])
            f.write('E '+f'{symtab[first]:0>6x}')

    
    # print('\n',symtab,'\n')
    # print(symnode)


def main():
    f = open('(test)SICXE.txt','r')
    charset(f)
main()