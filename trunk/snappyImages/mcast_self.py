
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

serverAddr = '\x00\x00\x01' # hard-coded address for Portal PC

# Sensor connection PINs on board.
flexSensor = (8,9,10,11,12,13,14,15)         #creating a table os strings.

# Device address bits, 3 bits in total from DIP switch

addrBit0 = 57
addrBit1 = 56
addrBit2 = 55


secondCounter = 0
buttonCount = 0

BUTTON_PIN = 26 # SW1

LED1 = 23
LED2 = 24
LED3 = 25
LED4 = 1


def makeInput(pin):
    setPinDir(pin, False)   # set direction of the pin as output
    setPinPullup(pin, True) # Power the pin for the DIP SW
    monitorPin(pin, True)   # Monitor for button press

@setHook(HOOK_STARTUP)
def startupEvent():
    """This is hooked into the HOOK_STARTUP event"""
    global buttonState, buttonTime
    global addreBits
    
    #findServer() ##in once server is ready 
     
    
    # Set PIN directions and initialize
    makeInput(addrBit0)
    makeInput(addrBit1)
    makeInput(addrBit2)
    setRate(1)             # set rate of polling for buttons 

    # Initialize button-detect variables
    addreBits = buttonRead()

def findServer():
    z=1
#mcastRpc(1,5,'svrAddr')

def serverAt(addr):
    global serverAddr
    #serverAddr = addr[:]


@setHook(HOOK_GPIN)
def buttonEvent(pinNum, isSet):
    """Hooked into the HOOK_GPIN event"""
    global addreBits
    if pinNum == (addrBit0 or addrBit1 or addrBit2):
        addreBits = buttonRead()

def buttonRead():    
    return int(str(readPin(addrBit0))+str(readPin(addrBit1))+str(readPin(addrBit2)), 2)




def doEverySecond():
    """Tasks that are executed every second"""
    z=0
    #showButtonCount()

@setHook(HOOK_100MS)
def timer100msEvent(currentMs):
    """Hooked into the HOOK_100MS event"""
    #global flexSensor
    
    # Read in the Analog values from the Sensors

    # read 8 sensor values
    sens =  str(readAdc(flexSensor[0])) + str(readAdc(flexSensor[1]))+str(readAdc(flexSensor[2]))
    #sens +=  str(i) + ':' + str(readAdc(flexSensor[i])) + '.'
        
       
    inpstr = str(addreBits) + '#' + sens    # package the Values in to one msg
    print "sens  = % s"   % sens
    rpc(serverAddr, "logEvent", inpstr , 100)    # Send package to server, Invoke Log event Function on the server  
    sendData()

def sendData():
    global inpstr 
    hello ="hello from straignt" 
    mcastRpc(1,5,"logEvent",hello)
    
    
    # Use a LONG (> 1 second) button press as a "counter reset"
"""#if buttonState == False:
        if buttonCount > 0:
            if currentMs - buttonTime >= 1000:
                buttonCount = 0
                reportButtonCount()"""

def setButtonCount(newCount):
    """Set the new button count"""
    global buttonCount
    buttonCount = newCount
    #showButtonCount()

def reportButtonCount():
    """Report to others that button press took place"""
    global buttonCount
    #showButtonCount()
    mcastRpc(1,2,'setButtonCount',buttonCount)
