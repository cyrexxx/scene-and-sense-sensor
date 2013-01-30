"""
This program and the accompanying materials
are made available under the terms of the Eclipse Public License v1.0
which accompanies this distribution, and is available at
http://www.eclipse.org/legal/epl-v10.html
Contributor: Synapse Wireless Inc., Huntsville, Alabama, 35806, USA
"""

"""
AtCommandInterpretor.py -- This module emulates API mode. 

The supported frame types are:
0x08 - AT Command
0x10 - Transmit Request
0x17 - Remote AT Command Request
0x88 - AT Command Response
0x8A - Modem Status
0x8B - Transmit Status
0x90 - Receive Packet
0x97 - Remote Command Response

The supported AT commands are:
AC - Apply Changes
AI - Association Indication
AP - API Mode
BD - UART Baud Rate
CH - Operating Channel
D6 - DIO6 Configuration
DB - Received Signal Strength
EE - Encryption Enable
EO - Encryption Options
FR - Software Reset
HV - Hardware Version
ID - Operating PAN ID
JV - Channel Verification
KY - Link Security Key
ND - Node Discovery
NH - Maximum Hops
NI - Node Identifier
NJ - Node Join Time
NK - Network Encryption Key
NP - Maximum RF Payload
NR - Network Reset
OI - Operating 16-bit PAN ID
OP - Operating Extended PAN ID
PL - Power Level
PM - Power Mode
SC - Scan Channels
SH - Serial Number High
SL - Serial Number Low
SY - Designate node as Coordinator
VR - Firmware Version
WR - Write

"""

from synapse.switchboard import *
from synapse.nvparams import *
from RF26x import *
from AtCommandDecoder import *

FIRMWARE_VERSION = '\x00\x01'

MCAST_GROUP = 1
MCAST_TTL = 2

# AT Command return values
ATOK = '\x00' 
ATERROR = '\x01'
ATBADCMD = '\x02'
ATBADPARA = '\x03'
ATTXERROR = '\x04'

# GPIO 
RADIO_STAT = 3
INTELLISENSE = DIO5
COMMISSIONING = DIO0
CTS = DIO7
RTS = DIO6

# Atmel processor registers
TCCR0A = 0x44
TCCR0B = 0x45
UCSR1A = 0xC8
UBRR1L = 0xCC
UBRR1H = 0xCD

# getStat
RADIO_RETRY_DISCARDED = 23

# nv parameters
SCAN_CHANNELS = 128
POWER_LEVEL = 129
BAUD_RATE = 130
CRYPTO_OPTIONS = 131
CHANNEL_VERIFY = 132
EXTENDED_PAN = 133
FLOW_CONTROL = 134
RADIO_RATE = 135

# global consts
COUNT_AI_MAX = 32
GOOD_LQ = 60
RSSI_TIMEOUT = 40


def defaults(isCoord):
    """Set factory default values for all devices.  Sets the baud rate
    of the UART to 115,200"""
    saveNvParam(BAUD_RATE, 1)
    verifyNvParam(NV_NETWORK_ID, 0x1c2c)
    verifyNvParam(NV_CHANNEL_ID, 4)
    verifyNvParam(NV_DEVICE_NAME_ID, None)
    
    if isCoord == True:
        verifyNvParam(NV_DEVICE_TYPE_ID, 'COORD')
    else:
        verifyNvParam(NV_DEVICE_TYPE_ID, None)
    
    verifyNvParam(SCAN_CHANNELS, 0x1ffe)
    verifyNvParam(POWER_LEVEL, 11)
    verifyNvParam(CRYPTO_OPTIONS, 0)
    verifyNvParam(CHANNEL_VERIFY, None)
    verifyNvParam(EXTENDED_PAN, None)
    verifyNvParam(FLOW_CONTROL, False)
    verifyNvParam(RADIO_RATE, 0)
    
    if rebootNode:
        reboot()
        
# NV Management
rebootNode = False
def verifyNvParam(param, val):
    global rebootNode
    if loadNvParam(param) != val:
        saveNvParam(param, val)
        rebootNode = True
        
# C function to calculate the checksum of a string         
csumFunc = '\xBD\x01\x40\xE0\x29\x50\x30\x40\xF9\x01\xB0\x85\xA7\x81\x1D\x91\x11\x23\x31' \
           '\xF0\xFD\x01\x01\x2F\x11\x91\x41\x0F\x0A\x95\xE1\xF7\x00\xE0\xF9\x01\x02\x83' \
           '\x40\x95\x41\x83\x01\xE0\x00\x83\xDB\x01\x08\x95'
def fastCalcCrc(command):
    return call(csumFunc, command)
    
def setBaudRate(rate):
    initUart(1, rate) 

# global variables
prevRetryDiscarded = 0
lostMaster = 0
startChanScan = True
txpkt = False
coord = None
connected = False
doFindCoord = False
chan = 0

@setHook(SnapConstants.HOOK_STARTUP)
def startupEvent():
    global chan, rebootNode, myPanId, myNodeId, myFlowControl, scanChannels, myBaudRate
    
    verifyNvParam(NV_UART_DM_TIMEOUT_ID, 0)
    verifyNvParam(NV_UART_DM_THRESHOLD_ID, 112)
    verifyNvParam(NV_UART_DM_INTERCHAR_ID, 20)
    verifyNvParam(NV_CARRIER_SENSE_ID, True)
    verifyNvParam(NV_COLLISION_DETECT_ID, False)
    verifyNvParam(NV_COLLISION_AVOIDANCE_ID, True)
    verifyNvParam(NV_SNAP_MAX_RETRIES_ID, 4)
    verifyNvParam(NV_MESH_ROUTE_AGE_MAX_TIMEOUT_ID, 60000)
    verifyNvParam(NV_MESH_INITIAL_HOPLIMIT_ID, 1)
    verifyNvParam(NV_MESH_MAX_HOPLIMIT_ID, 5)
    verifyNvParam(NV_SYS_PLATFORM_ID, 'RF266')
    verifyNvParam(NV_VENDOR_SETTINGS_ID, 1)
    
    if loadNvParam(POWER_LEVEL) is None:
        saveNvParam(POWER_LEVEL, 11)
        rebootNode = True       
    txPwr(loadNvParam(POWER_LEVEL))
    
    if loadNvParam(RADIO_RATE) is None:
        saveNvParam(RADIO_RATE, 0)
        rebootNode = True       
    setRadioRate(loadNvParam(RADIO_RATE))
    
    initUart(0, 1) # disable unused UART
    initWorkBuf()        
    
    if loadNvParam(BAUD_RATE) is None:
        saveNvParam(BAUD_RATE, 1)
        rebootNode = True       
    myBaudRate = loadNvParam(BAUD_RATE)
    setBaudRate(myBaudRate)
    
    if loadNvParam(SCAN_CHANNELS) is None:
        saveNvParam(SCAN_CHANNELS, 0x1ffe)
        rebootNode = True       
    scanChannels = loadNvParam(SCAN_CHANNELS)
    
    if loadNvParam(FLOW_CONTROL) is None:
        saveNvParam(FLOW_CONTROL, True)
        rebootNode = True       
    myFlowControl = loadNvParam(FLOW_CONTROL)
    
    if rebootNode:
        reboot()
    
    flowControl(1, myFlowControl)
    setPinDir(CTS, True)
    writePin(CTS, False)
    
    crossConnect(DS_STDIO, DS_UART1)
    uniConnect(DS_STDIO, DS_TRANSPARENT)
    stdinMode(1, False)
    crossConnect(DS_PACKET_SERIAL, DS_NULL) # for speed
    
    setPinDir(RADIO_STAT, True)
    writePin(RADIO_STAT, False)
   
    # Set up Associate LED output on pin 15
    setPinDir(INTELLISENSE, True)
    writePin(INTELLISENSE, True)
    poke(0x48, 0x80) # counter 0 ocr A 
    
    setPinDir(COMMISSIONING, False)
    monitorPin(COMMISSIONING, True)
   
    myPanId = loadNvParam(EXTENDED_PAN)
    myNodeId = loadNvParam(NV_DEVICE_NAME_ID)
    
    if loadNvParam(BAUD_RATE) is None:
        setChannel(4)
        setNetId(0x1c2c)
    
    elif myPanId is not None and loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
        chan = channelScanner()
        setChannel(chan)        
        
    sendDataString('\x8a\x00') # Modem status hardware reset
    
counter1s = 0
@setHook(SnapConstants.HOOK_1S)
def poll1s(msTick):
    global chan, coord, prevRetryDiscarded, lostMaster, startChanScan, counter1s
    
    # control radio status     
    if connected == True:
        # Turn on timer/counter 0 PWM for OC0B pin 15 
        poke(TCCR0A, 0x33) #mode
        poke(TCCR0B, 0x03) #clock source
    else:
        poke(TCCR0A, 0x00) #mode
        poke(TCCR0B, 0x00) #clock source
        writePin(INTELLISENSE, True)
    
    if loadNvParam(BAUD_RATE) is not None and myPanId is not None:
        if loadNvParam(NV_DEVICE_TYPE_ID) != 'COORD':
            if coord is None:
                if startChanScan == False:
                    # Trying to find the coordinator.  Go to the next channel.
                    bitmask = scanChannels
                    if bitmask != 0:
                        while True:
                            chan = (chan + 1) % 16
                            if ((2 ** chan) & bitmask) != 0:
                                setChannel(chan)
                                break
                                
                mcastRpc(MCAST_GROUP, MCAST_TTL, 'findCoord', myPanId)
                startChanScan = False
                
            else:
                # Check to see if we lost comm with the coordinator 
                counter1s += 1
                if counter1s > 5:
                    counter1s = 0
                    retryDiscarded = getStat(RADIO_RETRY_DISCARDED)
                    if retryDiscarded != prevRetryDiscarded:
                        lostMaster += 1
                        prevRetryDiscarded = retryDiscarded
                        
                if lostMaster >= 5:
                    sendDataString('\x8a\x03') # disassociated
                    coord = None
                    startChanScan = True
                    lostMaster = 0
                    
                    
rssiTime = 0
@setHook(SnapConstants.HOOK_100MS)
def poll100Ms(msTick):
    global rssiTime
    rssiTime = 0
    
    #if rssiTime < RSSI_TIMEOUT:
        #rssiTime += 1
    #else:
        #writePin(RADIO_STAT, False)
        
def rssiHandler():
    #global rssiTime
    pulsePin(RADIO_STAT, 4000, True)
    
    #writePin(RADIO_STAT, (getLq() < GOOD_LQ))
    #rssiTime = 0
        
startup = True
@setHook(SnapConstants.HOOK_10MS)
def poll10Ms(msTick):
    global startup
    if startup == True:
        startup = False
        if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
            sendDataString('\x8a\x06') # Modem status Coordinator started
    
def sendDataString(dataString):
    """ send data string to the local device via the UART """
    length = len(dataString)
    crc = fastCalcCrc(dataString[:])
    print  '\x7e' + chr(length >> 8) + chr(length) + dataString + chr(crc),

@setHook(SnapConstants.HOOK_RPC_SENT)
def rpcSentEvent():
    """ An rpc was sent to a destination.  Respond with a transmit status message """
    global txpkt
    
    if txpkt == True and coord is not None:
        txpkt = False
        # 16-bit address = 00 00
        # retry count = 00
        # delivery status = 00 - success
        # discovery status = 00 - no discovery overhead
        sendDataString('\x8b' + g_frameId + '\x00\x00' + '\x00\x00\x00')
        
delayedInitUart = False
@setHook(SnapConstants.HOOK_STDOUT)
def stdoutEvent():
    global delayedInitUart
    
    if delayedInitUart == True:
        delayedInitUart = False
        setBaudRate(myBaudRate)
        
@setHook(SnapConstants.HOOK_STDIN)
def stdinEvent(data):
    # Submit rx buffer to frameDecoder, until it's all used up   
    
    if getInfo(16) == DS_TRANSPARENT:
        txPacket('\x00', data)
    else:
        writePin(CTS, True)

        hasMore = True
        while hasMore:
            action_more = cRxFsm(data)
            hasMore = action_more & 0x00FF
            action = action_more >> 8
            if action == ACT_FRAME:
                processData()
                
        writePin(CTS, False)                
                
def processData():
    '''This is where frames are processed as they are received.  For lengthy processing
       intervals, asserting flow-control may be necessary.'''
    global coord, g_frameId, txpkt

    frame = wbFrameData()
    cmd = frame[0]
    
    if cmd == '\x08': # AT command
        g_frameId = frameId = frame[1]
        atCmd = frame[2:4]
        respStr = getAtCommandData(atCmd, frame[4:])
        sendDataString('\x88' + frameId + respStr)
            
    elif cmd == '\x17': # Remote AT command
        g_frameId = frameId = frame[1]
        atCmd = frame[2:4]
        rpc(frame[7:10], 'remoteAtCmd', frameId, frame[12:])
            
    elif cmd == '\x10': # Transmit
        g_frameId = frameId = frame[1]
        destAddress = frame[2:10]
        if destAddress == '\x00\x00\x00\x00\x00\x00\xff\xff':
            # broadcast
            mcastRpc(MCAST_GROUP, MCAST_TTL, 'txPacket', frameId, frame[14:])
            
        elif destAddress == loadNvParam(NV_MAC_ADDR_ID):
            # self addressed
            sendDataString('\x8b' + frameId + frame[10:12] + '\x02\x23\x00')
            
        else:
            target = None
            if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD' or (coord is not None and destAddress != '\x00\x00\x00\x00\x00\x00\x00\x00'):
                target = frame[7:10]
            elif coord is not None and destAddress == '\x00\x00\x00\x00\x00\x00\x00\x00' and frame[10:12] == '\xff\xfe':
                target = coord
                    
            if target is not None and rpc(target, 'txPacket', frameId, frame[14:]) == True:
                txpkt = True
            else:
                sendDataString('\x8b' + frameId + frame[10:12] + chr(loadNvParam(NV_SNAP_MAX_RETRIES_ID)) + '\x24\x00') # address not found
        
def getAtCommandData(atCmd, data):
    global chan, coord, myPanId, myNodeId, startChanScan, myFlowControl, scanChannels, delayedInitUart, myBaudRate
    
    dataLength = len(data)
    
    resp = atCmd 
    if atCmd == 'SY': # SYNAPSE AT COMMAND TO SET DEVICE TO A COORDINATOR
        if dataLength == 0:
            if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
                resp += ATOK + '\x01'
            else:
                resp += ATOK + '\x00'
        elif dataLength == 1:
            if data[0] == '\x00':
                saveNvParam(NV_DEVICE_TYPE_ID, None)
                resp += ATOK
            else:
                saveNvParam(NV_DEVICE_TYPE_ID, 'COORD')
                resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'CH': # Operating Channel (read-only)
        # Returns the 802.15.4 representation of the SNAP channel
        if dataLength == 0:
            if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
                resp += ATOK + chr((getChannel()+11)&0xff)
            elif not connected:
                resp += ATOK + '\x00'
            else:
                resp += ATOK + chr((getChannel()+11)&0xff)
        else:
            resp += ATBADPARA
    elif atCmd == 'OP': # Operating Extended PAN ID
        if dataLength == 0:
            if myPanId is not None:
                resp += ATOK + myPanId
            else:
                resp += ATOK + '\x00\x00\x00\x00\x00\x00\x00\x00'
        else:
            resp += ATBADPARA
    elif atCmd == 'OI': # Operating 16-bit PAN ID (read-only)
        if dataLength == 0:
            if myPanId is not None:
                resp += ATOK + chr((getNetId()&0xff00)>>8) + chr(getNetId()&0x00ff)
            else:
                resp += ATOK + '\x00\x00'
        else:
            resp += ATBADPARA
    elif atCmd == 'ID': # Operating PAN ID
        if dataLength == 0:
            if myPanId is not None:
                resp += ATOK + myPanId
            else:
                resp += ATOK + '\x00\x00\x00\x00\x00\x00\x00\x00'
        elif dataLength == 1 and data[0] == '\x00':
            myPanId = '\x00\x00\x00\x00\x00\x00' + chr((getNetId()&0xff00)>>8) + chr(getNetId()&0x00ff)
            resp += ATOK
        elif dataLength == 8:
            if data == '\x00\x00\x00\x00\x00\x00\x00\x00':
                data = '\x00\x00\x00\x00\x00\x00\x1c\x2c'
            myPanId = data
            if data[6:8] == '\xff\xff':
                setNetId(0x1c2c)
            else:
                setNetId((ord(data[6])<<8) + ord(data[7]))
                
            if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
                setChannel(channelScanner())
            else:
                coord = None
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'SC': # Scan Channels
        if dataLength == 0:
            resp += ATOK + chr((scanChannels&0xff00)>>8) + chr(scanChannels&0x00ff)
        elif dataLength == 2:
            scanChannels = (ord(data[0])<<8) + ord(data[1])
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'AP': # API mode
        if dataLength == 0:
            resp += ATOK + '\x01'
        else:
            resp += ATBADPARA
    elif atCmd == 'PL': # Power Level
        if dataLength == 0:
            power = loadNvParam(POWER_LEVEL)
            resp += ATOK + chr(power)
        elif dataLength == 1:
            power = ord(data[0])
            if power > 11: 
                power = 11
            saveNvParam(POWER_LEVEL, power)
            txPwr(power)
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'BD': # UART Baud Rate
        if dataLength == 0:
            resp += ATOK
            if myBaudRate == 1: 
                resp += '\x00\x00\x00\x07' # 115200
            else:
                resp += chr((myBaudRate&0xff00)>>8) + chr(myBaudRate&0x00ff)
        elif dataLength <= 4:
            if data == '\x00\x01\xC2\x00' or data == '\x01\xC2\x00' or data == '\x00\x00\x00\x07' or data == '\x07': # 115200 bps
                myBaudRate = 1
                resp += ATOK
                delayedInitUart = True
            else:
                myBaudRate = data
                resp += ATOK
                delayedInitUart = True
        else:
            resp += ATBADPARA
    elif atCmd == 'NI': # Node Identifier
        if dataLength == 0:
            if myNodeId == None:
                resp += ATOK + ' '
            else:
                resp += ATOK + myNodeId
        else:
            # remove trailing zeros
            i = dataLength - 1
            while i > 1:
                if data[i] != '\x00':
                    break
                i -= 1
            nodeId = data[:i+1]
            myNodeId = nodeId
            resp += ATOK
    elif atCmd == 'EE': # Encryption Enable
        if dataLength == 0:
            if loadNvParam(NV_CRYPTO_TYPE) == 0:
                resp += ATOK + '\x00'
            elif loadNvParam(NV_CRYPTO_TYPE) == 1:
                resp += ATOK + '\x01'
            else: 
                resp += ATBADPARA
        elif dataLength == 1:
            if data[0] == '\x00':
                saveNvParam(NV_CRYPTO_TYPE, '\x00')
                resp += ATOK
            elif data[0] == '\x01':
                saveNvParam(NV_CRYPTO_TYPE, '\x01')
                resp += ATOK
            else:
                resp += ATBADPARA
        else:
            resp += ATBADPARA
    elif atCmd == 'EO': # Encryption Options
        if dataLength == 0:
            options = loadNvParam(CRYPTO_OPTIONS)
            resp += ATOK + chr(options>>8) + chr(options & 0xff)
        elif dataLength == 2:
            saveNvParam(CRYPTO_OPTIONS, (ord(data[0])<<8) + ord(data[1]))
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'NK': # Network Encryption Key
        resp += ATBADPARA
    elif atCmd == 'KY': # Link Security Key
        if dataLength == 0:
            resp += ATBADPARA
        elif dataLength <= 16:
            key = data
            i = dataLength
            while i < 16:
                key += '\x00'
                i += 1
            saveNvParam(NV_CRYPTO_KEY, key)
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'NH': # Maximum Hops
        if dataLength == 0:
            resp += ATOK + chr(loadNvParam(NV_MESH_MAX_HOPLIMIT_ID))
        elif dataLength == 1:
            saveNvParam(NV_MESH_MAX_HOPLIMIT_ID, ord(data[0]))
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'JV': # Channel Verify
        if dataLength == 0:
            resp += ATOK + chr(loadNvParam(CHANNEL_VERIFY))
        elif dataLength == 1:
            saveNvParam(CHANNEL_VERIFY, ord(data[0]))
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'VR': # Firmware Version
        if dataLength == 0:
            resp += ATOK + FIRMWARE_VERSION
        else:
            resp += ATBADPARA
    elif atCmd == 'NP': # Maximum RF Payload
        if dataLength == 0:
            resp += ATOK + '\x00\x54' # max payload 66 bytes?
        else:
            resp += ATBADPARA
    elif atCmd == 'SH': # Serial Number High
        if dataLength == 0:
            
            resp += ATOK + loadNvParam(NV_MAC_ADDR_ID)[:4]
        else:
            resp += ATBADPARA
    elif atCmd == 'SL': # Serial Number Low
        if dataLength == 0:
            resp += ATOK + loadNvParam(NV_MAC_ADDR_ID)[4:]
        else:
            resp += ATBADPARA
    elif atCmd == 'DB': # Received Signal Strength
        if dataLength == 0:
            resp += ATOK + chr(getLq())
        elif dataLength == 1:
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'AI': # Association Indication
        if dataLength == 0:
            if connected:
                resp += ATOK + '\x00' # Successfully formed or joined a network
            else:
                resp += ATOK + '\xff'  # Scanning for a network
                if loadNvParam(NV_DEVICE_TYPE_ID) != 'COORD':
                    # do something!
                    pass
        else:
            resp += ATBADPARA
    elif atCmd == 'AC': # Apply Changes
        if dataLength == 0:
            resp += ATOK
        else:
            resp += ATBADPARA
    elif atCmd == 'WR': # Write
        if dataLength == 0:
            resp += ATOK
            saveNvParam(EXTENDED_PAN, myPanId)
            saveNvParam(NV_DEVICE_NAME_ID, myNodeId)
            saveNvParam(NV_NETWORK_ID, getNetId())
            saveNvParam(FLOW_CONTROL, myFlowControl)
            saveNvParam(SCAN_CHANNELS, scanChannels)
            saveNvParam(BAUD_RATE, myBaudRate)
        else:
            resp += ATBADPARA
    elif atCmd == 'FR': # Software reset
        if dataLength == 0:
            resp += ATOK
            reboot()
        else:
            resp += ATBADPARA
    elif atCmd == 'NR': # Network Reset
        if dataLength == 0:
            resp += ATOK
            if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
                chan = channelScanner()
                setChannel(chan)
            else:
                coord = None
                startChanScan = True
                sendDataString('\x8a\x03')
        else:
            resp += ATBADPARA
    elif atCmd == 'ND': # Node Discovery
        if dataLength == 0:
            resp += ATOK + getNodeInfo(myPanId, None)            
            if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
                mcastRpc(MCAST_GROUP, MCAST_TTL, 'callback', 'displayNodeInfo', 'getNodeInfo', myPanId, None)
            elif coord is not None:
                rpc(coord, 'callback', 'displayNodeInfo', 'getNodeInfo', myPanId, None)
        else:
            mcastRpc(MCAST_GROUP, MCAST_TTL, 'callback', 'displayNodeInfo', 'getNodeInfo', myPanId, data)
    elif atCmd == 'HV': # Hardware Version
        if dataLength == 0:
            resp += ATOK + chr(getInfo(5)) + '.' + chr(getInfo(6)) + '.' + chr(getInfo(7))
        else:
            resp += ATBADPARA
    elif atCmd == 'PM': # Power Mode
        if dataLength == 0:
            resp += ATOK + '\x01'            
        else:
            resp += ATBADPARA
    elif atCmd == 'NJ': # Node Join Time
        if dataLength == 0:
            resp += ATOK + '\xff'            
        else:
            resp += ATBADPARA
    elif atCmd == 'D6': # DIO6 Configuration 
        # DIO6 is pin 16. A.K.A RTS
        if dataLength == 0:
            if myFlowControl == True:
                resp += ATOK + '\x01'
            else:
                resp += ATOK + '\x00'
        elif dataLength == 1:
            dio6 = ord(data[0])
            if dio6 == 0:
                # disabled
                setPinDir(RTS, False)
                myFlowControl = False
                flowControl(1, myFlowControl)
                resp += ATOK
            elif dio6 == 1:
                # RTS flow control
                setPinDir(RTS, False)
                myFlowControl = True
                flowControl(1, myFlowControl)
                resp += ATOK
            elif dio6 == 3:
                # Digital input
                setPinDir(RTS, False)
                myFlowControl = False
                flowControl(1, myFlowControl)
                resp += ATOK
            elif dio6 == 4:
                # Digital output low
                setPinDir(RTS, True)
                writePin(RTS, False)
                myFlowControl = False
                flowControl(1, myFlowControl)
                resp += ATOK
            elif dio6 == 5:
                # Digital output high
                setPinDir(RTS, True)
                writePin(RTS, True)
                myFlowControl = False
                flowControl(1, myFlowControl)
                resp += ATOK
            else:
                resp += ATBADPARA
        else:
            resp += ATBADPARA
    else:
        resp += ATBADCMD # Invalid command
        
    return resp

def remoteAtCmd(frameId, data):
    """ RPC method to perform AT command on remote device """
    options = ord(data[0])
    resp = getAtCommandData(data[1:3], data[3:])
    if options & 0x01 == 0:
        rpc(rpcSourceAddr(), 'remoteAtResp', frameId, resp)
    
def remoteAtResp(frameId, data):
    """ RPC response method for remote AT command """
    sendDataString('\x97' + frameId + '\x00\x00\x00\x00\x00' + rpcSourceAddr() + '\xff\xfe' + data)

def getNodeInfo(panId, device):
    """ format response for node info AT command """
    if panId == myPanId:
        if device is None or device == loadNvParam(NV_DEVICE_TYPE_ID):
            if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD': 
                deviceType = '\x00'
            else: deviceType = '\x01'
            
            resp = '\x00\x00' #MY
            resp += '\x00\x00\x00\x00\x00' + localAddr()   # SH / SL
            if myNodeId == None:
                resp += ' \x00'
            else:
                resp += myNodeId + '\x00'       # NI
            resp += '\xff\xfe'                                  # parent network address (2 bytes)
            resp += deviceType                                  # device type (0=coord, 1=router)
            resp += '\x00'                                      # status (reserved) (1 byte)
            resp += '\xc1\x05'                                  # profile id (2 bytes)
            resp += '\x00\x00'                                  # manufacturer id (2 bytes)
            return resp
        else:
            return None
    else:
        return None
        
def displayNodeInfo(info):
    """ Callback for response to NI command """
    if info is not None:
        sendDataString('\x88' + g_frameId + 'ND' + ATOK + info)
    
def findCoord(extendedPan):
    """ RPC method to pair device to coordinator """
    global connected
    
    
    if loadNvParam(NV_DEVICE_TYPE_ID) == 'COORD':
        if extendedPan == myPanId:
            rssiHandler()
            rpc(rpcSourceAddr(), 'coordFound')
            connected = True
            
def coordFound():
    """ RPC response to pair device to coordinator """
    global coord, connected, doFindCoord
    
    rssiHandler()
    
    connected = True
    doFindCoord = False
    coord = rpcSourceAddr()
    sendDataString('\x8a\x02')
        
def txPacket(packetType, data):
    """ RPC method to send data to a device """
    rssiHandler()
    sourceAddr = rpcSourceAddr()
    
    dataString = '\x90'
    dataString += '\x00\x00\x00\x00\x00' + sourceAddr # 64-bit address
    dataString += sourceAddr[1:]
    dataString += '\x01' # receive options, packet acknowledged
    dataString += data
    sendDataString(dataString)
    
def channelScanner():
    """ This method is used by the coordinator to find a channel to use """
    scan1 = scanEnergy()
    
    chanMask = scanChannels
    currChan = getChannel()   
    
    sum = 0
    index = 0
    min = 0
    minIndex = -1
    while index < len(scan1):
        if ((2 ** index) & chanMask) != 0:
            sum += ord(scan1[index])
            if min < ord(scan1[index]):
                min = ord(scan1[index])
                minIndex = index
        index += 1        
    mean = sum/len(scan1)    
    
    index = 0
    while index < len(scan1):
        if ((2 ** index) & chanMask) != 0 and ord(scan1[index]) > mean:
            return index
        index += 1
        
    return minIndex

def getCoord():
    """ Helper method to see if this node has been paired with an coordinator """
    if coord is None:
        return 'No Coordinator'
    else:
        return 'Coordinator is present'
        
    