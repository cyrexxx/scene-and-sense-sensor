"""
Title:    Master device to read poll slaves 
Author:   Kartik Karuna <kartik@kth.se>,Samarth Deo <samarthd@kth.se>
File:     $Id: Flex_Master.py ,v 1.2 2013/01/015 17:07:18 Kartik Exp $
Software: synapse IDE
Hardware: RF266 , Ver 2.4.33???

Description:
    this code acts as a serial line replacement. All data received
    from the DIN(serial) pin is transmitted on the RF, and when RF data is 
    received, it is sent out on the DOUT (serial) pin.  

Include Files (Libs)
     switchboard
     synapse.nvparams 
"""

"""Sample script for the multi-drop serial master device.
   Load this script into the MASTER device.  It will broadcast serial data to the SLAVE devices,
   and periodically announce its MASTER status to all.
"""

from switchboard import *

# Maximum number of hops allowed for multicast forwarding
numHops = 4

secondCounter = 0
@setHook(HOOK_STARTUP)
def startup():
    # Initialize UART
    initUart(1, 9600)           # 9600 baud
    flowControl(1, False)       # No flow control

    # Connect UART to transparent data endpoint.
    #   The default transparent configuration is broadcast
    crossConnect(DS_UART1, DS_TRANSPARENT)
    
    # Enable bridge connections on the other UART
    crossConnect(DS_UART0, DS_PACKET_SERIAL)

def announceMaster():
    """Broadcast master status.  This allows slaves to learn our address, so they can unicast back."""
    mcastRpc(1, numHops, 'master')

@setHook(HOOK_100MS)    
def poll100ms(mstick):
    global secondCounter
    
    # Periodically announce 'master' status to all slaves
    secondCounter += 1
    if secondCounter >= 10:
        announceMaster()
        secondCounter = 0
