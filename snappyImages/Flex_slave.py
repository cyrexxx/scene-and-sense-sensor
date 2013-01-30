"""/****************************************************************************
Title:    Slave device to read flexSensor values 
Author:   Kartik Karuna <kartik@kth.se>,Samarth Deo <samarthd@kth.se>
File:     $Id: Flex_slave.py ,v 1.2 2013/01/015 17:07:18 Kartik Exp $
Software: synapse IDE
Hardware: SM700 , Ver 2.4.33

Description:
    this code reads Analog values for 8 flex sensors and encodes it 
    into one message and sends it over the air to the Server  
Include Files (Libs)
     synapse.evalBase 
     synapse.nvparams 
*****************************************************************************/"""

#Lib
#from synapse.evalBase import *
#from synapse.nvparams import *
#from string import *
from synapse.platforms import *

serverAddr = '\x00\x00\x01' # hard-coded address for Portal PC
# check if compiled for SM700 
if platform != "SM700":
    compileError #script only valid on SM700
    
# Sensor connection PINs on board.

ADC_0 = 8
ADC_1 = 9 
ADC_2 = 10
ADC_3 = 11
ADC_4 = 12 
ADC_5 = 13
ADC_6 = 14
ADC_7 = 15 
scount =0 
acount =0
 

# Device address bits, 3 bits in total from DIP switch

addrBit0 = 57
addrBit1 = 56
addrBit2 = 55

def makeInput(pin):
    setPinDir(pin, False)   # set direction of the pin as output
    setPinPullup(pin, True) # Power the pin for the Photocell
    monitorPin(pin, True)   # Monitor for button press
    
# Things to do at startup
@setHook(HOOK_STARTUP)
def startupEvent():
    global addreBits
    #findServer() ##in once server is ready 
    
    # Set PIN directions and initialize
    makeInput(addrBit0)
    makeInput(addrBit1)
    makeInput(addrBit2)
    setRate(1)             # set rate of polling for buttons 
    

    #convert address bits to intiger number 
    addreBits = buttonRead()
    #mcastRpc
   
# Tries to find an active server
def findServer():
    mcastRpc(1,5,'svrAddr')
    
# A server is announced to th slae , save its address 
def serverAt(addr):
    global serverAddr
    serverAddr = addr[:]
    
def setThreshold(newThreshold):
    #Use this to change the 'darkness' threshold from the default of 85%
    global darkThreshold
    darkThreshold = newThreshold

def setRange(newRange):
    #Use this to change the default 'required light range' from the default of 100 ADC counts
    global requiredRange
    requiredrange = newRange
    
# Do every 10 MS    
@setHook(HOOK_1S)
def timer1SEvent(currentMs):
    global sens
    
    # Read in the Analog values from the Sensors
<<<<<<< .mine
    
    rpc(serverAddr, "logEvent", inpstr , 100)
    
=======
>>>>>>> .r23
<<<<<<< .mine
    
    #sens =  ':' +'1'+'#' + str(readAdc(ADC_0))  + '.'+'2'+'#' +  str(readAdc(ADC_1))+ '.' + '3'+'#' + str(readAdc(ADC_2)) + '.'+'4'+ '#' +  str(readAdc(ADC_3)) + '.'+'5'+ '#' +  str(readAdc(ADC_4)) + '.'+'6'+'#'+ str(readAdc(ADC_5)) + '.'+'7'+'#'+ str(readAdc(ADC_6)) + '.'+'8'+'#'+ str(readAdc(ADC_7))
    sens =   '1.'+ sadc0 + '#2.'+  sadc1+ '#3.'+ sadc2 +'#4.'+  sadc3 + '#5.'+ sadc4 + '#6.'+sadc5 + '#7.'+ sadc6 + '#8.'+ sadc7
=======
    # read 8 sensor values
    sens =  ':' +'1'+'#' + str(readAdc(ADC_0))  + '.'+'2'+'#' +  str(readAdc(ADC_1))+ '.' + '3'+'#' + str(readAdc(ADC_2)) + '.'+'4'+ '#' +  str(readAdc(ADC_3)) + '.'+'5'+ '#' +  str(readAdc(ADC_4)) + '.'+'2'+ str(readAdc(ADC_5)) + '.'+'2'+ str(readAdc(ADC_6)) + '.'+'2'+ str(readAdc(ADC_7))
>>>>>>> .r23
       
    inpstr = str(addreBits) + '#' + sens    # package the Values in to one msg
    print "sens  = % s"   % sens
    rpc(serverAddr, "logEvent", inpstr , 100)    # Send package to server, Invoke Log event Function on the server  
    sendData()
    
def sendData():
    global inpstr 
    hello ="hello from straignt" 
    mcastRpc(1,5,"logEvent",sens)
    
   
   
@setHook(HOOK_1MS)
def timer1MSEvent(currentMs): 
    global radc0, radc1, radc2, radc3, radc4, radc5, radc6, radc7
    global acount 
    
    if acount==0:
        radc0= readAdc(ADC_0)
    elif acount ==1:
        radc1= readAdc(ADC_1)
    elif acount ==2:
        radc2= readAdc(ADC_2)
    elif acount ==3:
        radc3= readAdc(ADC_3)
    elif acount ==4:
        radc4= readAdc(ADC_4)
    elif acount ==5:
        radc5= readAdc(ADC_5)
    elif acount ==6:
        radc6= readAdc(ADC_6)
    elif acount ==7:
        radc7= readAdc(ADC_7)
        acount =-1
    
    acount+=1
    
@setHook(HOOK_10MS)
def timer10MSEvent(currentMs):
    global sadc0, sadc1, sadc2, sadc3, sadc4, sadc5, sadc6,sadc7
    global scount
    # read 8 sensor values
    
    
    scount+=1
    
    if scount == 5 :
       sadc0= str(radc0)
       sadc1= str(radc1)
       sadc2= str(radc2)
       sadc3= str(radc3)
       sadc4= str(radc4)
       sadc5= str(radc5)
       sadc6= str(radc6)
       sadc7= str(radc7)
       scount = 0
    
@setHook(HOOK_GPIN)
def buttonEvent(pinNum, isSet):    
     #Action taken when the on-board buttton is pressed (i.e. change address )
     global addreBits
     if pinNum == (addrBit0 or addrBit1 or addrBit2):
        addreBits = buttonRead()
    
def buttonRead():    
    return int(str(readPin(addrBit0))+str(readPin(addrBit1))+str(readPin(addrBit2)), 2)

@setHook(HOOK_RPC_SENT) #This is hooked into the HOOK_RPC_SENT event that is called after every RPC
def rpcSentEvent():
    sendData()
    