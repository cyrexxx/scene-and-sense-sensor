"""
Title:    Master device to read poll slaves 
Author:   Kartik Karuna <kartik@kth.se>,Samarth Deo <samarthd@kth.se>
File:     $Id: Flex_Master.py ,v 1.2 2013/01/015 17:07:18 Kartik Exp $
Software: synapse IDE
Hardware: RF266 , Ver 2.4.33???

Description:
    this code acts as a Master. All data received from the DIN(serial)
     pin is transmitted on the RF, and when RF data is 
    received, it is sent out on the DOUT (serial) pin.  

Include Files (Libs)
     switchboard
     synapse.nvparams
     synapse.platforms 
"""

"""
   Load this script into the MASTER device .  It will get data from the SLAVE devices,
   and periodically announce its MASTER status to all.
"""

from synapse.platforms import *
from switchboard import *

# Maximum number of hops allowed for multicast forwarding
numHops = 4
serverAddr = '\x00\x00\x01'

if platform != "RF200":
    compileError       #script only valid on RF266 /RF200


secondCounter = 0

# Things to do at startup
@setHook(HOOK_STARTUP)
def startup():

    # Initialize UART
    initUart(1, 9600)           # 9600 baud
    flowControl(1, False)       # No flow control

    # Connect UART to transparent data endpoint.
    #   The default transparent configuration is broadcast
    #crossConnect(DS_STDIO, DS_TRANSPARENT)
    crossConnect(DS_STDIO, DS_UART1)
    # Enable bridge connections on the other UART
    #crossConnect(DS_UART0, DS_PACKET_SERIAL)
    
    
def echo(obj):
    print str(obj)
  
# function called by slaves for send data to serial port
def printData(senstr):
     strflexdat = str(senstr)        # may not be needed check
     print strflexdat
     print "\n" 
     portaladd = '\x00\x00\x01'      # for debugging    
     mst='master '+strflexdat        # for debugging 
     rpc(portaladd,"logEvent",mst)   # for debugging

#Devices who WANT a Master call this function to fetch Master's address ,returns Master's address
def svrAddr():
    rpc(rpcSourceAddr(), 'serverAt', localAddr())
    
#Broadcast master status.  This allows slaves to learn our address, so they can unicast back.
def announceMaster():
    mcastRpc(1, numHops, 'serverAt',localAddr())

#keep track of slaves found
def slaveFound(saddres):
    global slaves_connected
    slaves_connected+=','+saddres
    

@setHook(HOOK_1S)    
def poll1ms(mstick):
    global secondCounter
    
    # Periodically announce 'master' status to all slaves
    secondCounter += 1
    if secondCounter >= 5:
        announceMaster()
        rpc(serverAddr , "logEvent",slaves_connected)
        secondCounter = 0
