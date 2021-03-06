from classes import *
import re
import copy

global current_scope
current_scope = "GLBL"

labelPat = r'\.LABEL[0-9]*'
whenEndPat = r'\.WLEND[0-9]*'
lendPat = r'LEND[0-9]*'

filename = file_processor("../Compiler/Intermediate.sdk")
tokens = Iterator(filename.getToks())

runTokens = Iterator(filename.getToks())

global glbl_sym_table
glbl_sym_table = SymbolTable('GLBL', None)
symtab_add(glbl_sym_table)
stack = Stack()
global isInExpression
isInExpression = False
global isInFunction
isInFunction = False
current_scope = "GLBL"
global recentPopFun
global whenStack
whenStack= Stack()

def TYP():
    global current_scope
    tokens.next() #this should pop off "TYP"
    varType = tokens.next() #pushes "INT, FLT, BOOL" onto stack
    identifier = tokens.next() #variable identifier ("a", "b", "c")
    if varType == "stack":
        newStack = Stack()
        dict_of_symbolTabs[current_scope].add(identifier, newStack)
    else:
        var = Variable(identifier, None, varType)
        dict_of_symbolTabs[current_scope].add(identifier, var)


def FUN():
    tokens.next()#pop FUN
    name = tokens.next() #name of function
    currentFunction = Function(tokens.next(), name) #return type
    while (tokens.next() == "PAR"):
        currentFunction.addParam(tokens.next(), tokens.next())
    currentFunction.startPC = tokens.counter
    dict_of_functions[name] = currentFunction
    while tokens.current() != "FUNEND":
        tokens.next()
    tokens.next()#pop End

def CALL():
    currentFunction = copy.deepcopy(dict_of_functions[tokens.next()])#functions should only be declared in global
    while tokens.next() == "PAR": #add all parameters
        global current_scope
        nextValue = tokens.next()
        try:
            if dict_of_symbolTabs[current_scope].lookup(nextValue) is not None:
                nextValue = dict_of_symbolTabs[current_scope].lookup(nextValue).getValue()
        except ValueError:
            print("value Not Found")

        currentFunction.setParamValues(nextValue)

    currentFunction.returnPC(tokens.getCounter()-1)#set return PC

    name = currentFunction.getName()
    counter = 0
    while (name + str(counter)) in dict_of_symbolTabs:
        counter += 1



    currentFunction.setName(name + str(counter))

    symbTable = SymbolTable(name + str(counter), current_scope)
    for key in currentFunction.getParams():
        symbTable.add(key, currentFunction.getParams()[key])

    dict_of_symbolTabs[name + str(counter)] = symbTable
    current_scope = name + str(counter) #set current_scope to the name of the function + number
    stack.push(currentFunction)

    tokens.setCounter(currentFunction.getStartPC())
    global isInExpression
    if isInExpression:
        main()

def RTRN():
    global current_scope
    global isInExpression
    global recentPopFun
    tokens.next() #pop RTRN
    exitedFun = stack.pop() #pop the function from the stack
    recentPopFun = copy.deepcopy(exitedFun)
    stack.push(dict_of_symbolTabs[exitedFun.getName()].lookup(tokens.next()).getValue()) #push the returned value
    tokens.setCounter(exitedFun.getReturnPC())
    current_scope = dict_of_symbolTabs[exitedFun.getName()].getPrevScope()

def LABL_TRACK():
    while runTokens.current() != "SDKEND":
        label = runTokens.current()
        global current_scope
        if re.match(labelPat, label):
            # print "Current Scope: " + current_scope
            current_label = Label(runTokens.current().replace(".", ""), runTokens.getCounter()+1, current_scope)
            # ltermnum = label[:-1]
            current_scope = label.replace(".", "")
        if re.match(lendPat, label):
            # print "Exit Scope: " + current_scope
            current_scope = dict_of_symbolTabs[current_scope].getPrevScope()
        runTokens.next()
    current_scope = "GLBL"


def STARTEX():
    global isInExpression
    isInExpression = True

    while tokens.current() != "ENDEX":
        nextToken = tokens.next()
        if nextToken == "PUSH":
            varName = tokens.next()
            if re.match(r'[+-]?(\d+(\.\d*)?|\.\d+)', varName):
                stack.push(eval(varName))
            else:
                try:
                    stack.push(dict_of_symbolTabs[current_scope].lookup(varName).getValue())

                except:
                    print("Symbol not found")

        elif nextToken == "ADD":
            result = stack.pop() + stack.pop()
            stack.push(result)
        elif nextToken == "SUB":
            first = stack.pop()
            result = stack.pop() - first
            stack.push(result)
        elif nextToken == "MUL":
            result = stack.pop() * stack.pop()
            stack.push(result)
        elif nextToken == "DIV":
            first = stack.pop()
            result = stack.pop() / first
            stack.push(result)
        elif nextToken == "GT":
            top = stack.pop()
            if stack.pop() > top:
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "LT":
            top = stack.pop()
            if stack.pop() < top:
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "GE":
            top = stack.pop()
            if stack.pop() >= top:
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "LE":
            top = stack.pop()
            if stack.pop() <= top:
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "EEQL":
            if stack.pop() == stack.pop():
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "NEQL":
            if stack.pop() != stack.pop():
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "NOT":
            if stack.pop() >= 1:
                stack.push(0)
            else:
                stack.push(1)
        elif nextToken == "SDKPO":
            stackObj = dict_of_symbolTabs[current_scope].lookup(tokens.next())
            stack.push(int(stackObj.pop()))
        elif nextToken == "EQL":
            nextToken = tokens.next()
            try:
                varObj = dict_of_symbolTabs[current_scope].lookup(nextToken)
                varObj.setValue(stack.pop())
            except ValueError:
                print("Identifier not found")
        elif nextToken == "AND":
            if stack.pop() and stack.pop():
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "OR":
            if stack.pop() or stack.pop():
                stack.push(1)
            else:
                stack.push(0)
        elif nextToken == "CALL":
            #tokens.setCounter(tokens.getCounter()-1)
            CALL()
            global recentPopFun
            if recentPopFun.getName()[-1:] == 0:
                print "RECENT POP FUN: " + recentPopFun.getName()
                isInExpression = False

    tokens.next()


def FUNEND():
    finishedFunction = stack.pop()
    tokens.setCounter(finishedFunction.getRetrunPC())

def LABL():
    lname = tokens.current().replace(".", "")
    global current_scope
    current_scope = lname
    tokens.next()

def CMP():
    if stack.pop() >= 1:
        tokens.next()
    else:
        global current_scope
        while tokens.current() != "LOOPLEND"+str(current_scope[-1:]):
            tokens.next()
def JMP():
    tokens.next()
    label = tokens.next()
    global current_scope
    current_scope = label
    dict_of_symbolTabs[label].emptyTable()
    tokens.setCounter(dict_of_labels[label].getStart())

def JEQ():
    if stack.pop() >= 1:
        tokens.next()
        global current_scope
        global isInFunction
        current_scope = tokens.next()
        tokens.setCounter(dict_of_labels.get(current_scope).getStart())
    else:
        tokens.next()
        curr_scope = tokens.current()
        num = curr_scope[-1:]
        while tokens.current() != "LEND"+str(num) :
            tokens.next()


def WHEN():
    global whenStack
    global current_scope
    whenStack.push(current_scope)
    tokens.next()

def WLEND():
    while tokens.current() != "ENDW":
        tokens.next()
    #dict_of_symbolTabs[current_scope].emptyTable()

def LOOPLEND():
    global current_scope
    current_scope = dict_of_symbolTabs[current_scope].getPrevScope()
    tokens.next()

def PRNT():
    expression = stack.pop()
    print str(expression)
    tokens.next()

def SDKPU():
    tokens.next()#pop SDKPU
    name = tokens.next() #name of stack
    currentStack = dict_of_symbolTabs[current_scope].lookup(name) #return type
    currentStack.push(tokens.next())


def SDKPO():
    tokens.next()#pop SDKPU
    name = tokens.next() #name of stack
    currentStack = dict_of_symbolTabs[current_scope].lookup(name) #return type
    currentStack.pop()

def main():
    global isInExpression
    if not isInExpression:
        LABL_TRACK()
    while tokens.current() != "SDKEND":
        nextToken = tokens.current()
        #print(nextToken)
        if nextToken == "TYP":
            TYP()
        elif nextToken == "FUN":
            FUN()
        elif nextToken == "CALL":
            CALL()
        elif nextToken == "RTRN":
            RTRN()
            if isInExpression:
                return
        elif nextToken == "STRTEX":
            STARTEX()
        elif nextToken == "FUNEND":
            FUNEND()
        elif re.match(labelPat, nextToken):
            LABL()
        elif nextToken == "CMP":
            CMP()
        elif nextToken == "JMP":
            JMP()
        elif nextToken == "JEQ":
            JEQ()

        elif nextToken == "LEND"+current_scope[-1:]:
            WLEND()
        elif nextToken == "LOOPLEND"+current_scope[-1:]:
            LOOPLEND()
        elif nextToken == "ENDPRNT":
            PRNT()
        elif nextToken == "WHEN":
            WHEN()
        elif nextToken == "SDKPU":
            SDKPU()
        elif nextToken == "SDKPO":
            SDKPO()
        else:
            tokens.next()
    #print dict_of_symbolTabs
#Call the main method. Starts runtime.
main()
