"""/****************************************************************************
Title:    Slave device to read flexSensor values 
Author:   Kartik Karuna <kartik@kth.se>,Samarth Deo <samarthd@kth.se>
File:     $Id: Flex_slave.py ,v 1.2 2013/01/015 17:07:18 Kartik Exp $
Software: synapse IDE
Hardware: SM700 , Ver 2.4.33

Description:
    this code reads Analog values for 8 flex sensors and encodes it 
    into one message and sends it over the air to the Server 
    Slave periodically searches for master, if none are found , it send
    the data to Portal. 
Include Files (Libs)
     synapse.nvparams
     synapse.platforms 
*****************************************************************************/"""

#Lib
from synapse.platforms import *
from synapse.nvparams import *
#from string import *

serverAddr = '\x00\x00\x01'  # hard-coded address for Portal (PC/MAC)

if platform != "SM700":
    compileError        #script only valid on SM700


# Device address bits, 3 bits in total from DIP switch

addrBit0 = 10     # KB5
addrBit1 = 9      #TMR1
addrBit2 = 27     #TMR2

def makeInput(pin):
    setPinDir(pin, False)   # set direction of the pin as output
    monitorPin(pin, True)   # Monitor for button press
  
    
# Things to do at startup
@setHook(HOOK_STARTUP)
def startupEvent():
    global addreBits
    global acount 
    acount = 0
    
    findServer() ##in once server is ready 
    
    # Set PIN directions and initialize
    
    makeInput(addrBit0)
    makeInput(addrBit1)
    makeInput(addrBit2)
    setRate(1)             # set rate of polling for buttons 
 
    addreBits = buttonRead() #initialize buttons, get ADD bits 
    
       
# Tries to find an active server
def findServer():
    mcastRpc(1,5,'svrAddr')
    
# A server is announced to th slae , save its address 
def serverAt(addr):
    global serverAddr,addset
    serverAddr = addr[:]
    addset='set '+str(serverAddr)
    mcastRpc(1,5,"logEvent",addset)
    
#def setThreshold(newThreshold):
    #Use this to change the  threshold from the default #Not used #future
    #global Threshold
    #Threshold = Threshold

#def setRange(newRange):
    #Use this to change the default 'required light range' from the default #Not used #future
    #global requiredRange
    #requiredrange = newRange
    
# Do every 10 MS    
@setHook(HOOK_10MS)
def timer10MSEvent(currentMs):
    global sens,inpstr
    
    # Read in the 8 sensor analog values from the Sensors
    # formating :sensor_number#ADC_value. .......
    sens =  ':1#' + str(ADC_0)  + '.2#' +  str(ADC_1) + '.3#' + str(ADC_2) + '.4#' +  str(ADC_3) + '.5#' +  str(ADC_4) + '.6#'+ str(ADC_5) + '.7#'+ str(ADC_6) + '.8#'+ str(ADC_7)+'.'
  
    # formating  Slave_address + sens (:sensor_number#ADC_value. .......)
    inpstr= str(addreBits) + sens    # package the Values in to one msg
    sendData(inpstr)                     #call function to broadcast data
    
#fuct to broadcast received data to portal or master     
def sendData(mdata):
    if serverAddr == '\x00\x00\x01':      # if no Marste is found send Msg to portal 
       rpc(serverAddr,"logEvent",mdata)
    else:                                 # if master found send data only to master
       rpc(serverAddr, "printData", mdata)
  
# Do every 1 MS  
@setHook(HOOK_1MS)
def timer1MSEvent(currentMs):
    global ADC_0,ADC_1,ADC_2,ADC_3,ADC_4,ADC_5,ADC_6,ADC_7
    global acount 
    
    # reading each ADC once every 9 MS
    # Using Vref=1.6 V
    if acount == 0:
        ADC_0 = readAdc(9)    #ADC 0
    elif acount == 1:
        ADC_1 = readAdc(10)   #ADC 1
    elif acount == 2:
        ADC_2 = readAdc(11)   #ADC 2
    elif acount == 3:
        ADC_3 = readAdc(12)   #ADC 3
    elif acount == 4:
        ADC_4 = readAdc(13)   #ADC 4
    elif acount == 5:
        ADC_5 = readAdc(14)   #ADC 5
    elif acount == 6:
        ADC_6 = readAdc(15)   #ADC 6
    elif acount == 7:
        ADC_7 = readAdc(16)   #ADC 7
        acount =-1    
    
    acount+=1
       
# Do every time there is a change in any monitored PIN 
@setHook(HOOK_GPIN)
def buttonEvent(pinNum, isSet):    
     #Action taken when the on-board buttton is pressed (i.e. change address )
     global addreBits
     if pinNum == (addrBit0 or addrBit1 or addrBit2):
        addreBits = buttonRead()
    
    
#convert address bits to intiger number 
def buttonRead():
    return ((4*(readPin(addrBit0))) +(2*(readPin(addrBit1)))+(1*(readPin(addrBit2))))
    
"""
@setHook(HOOK_RPC_SENT) #This is hooked into the HOOK_RPC_SENT event that is called after every RPC
def rpcSentEvent():
    k=2"""
    
    