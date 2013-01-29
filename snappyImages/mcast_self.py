# Copyright (C) 2011 Synapse Wireless, Inc.
# Subject to your agreement of the disclaimer set forth below, permission is given by Synapse Wireless, Inc. ("Synapse") to you to freely modify, redistribute or include this SNAPpy code in any program. The purpose of this code is to help you understand and learn about SNAPpy by code examples.
# BY USING ALL OR ANY PORTION OF THIS SNAPPY CODE, YOU ACCEPT AND AGREE TO THE BELOW DISCLAIMER. If you do not accept or agree to the below disclaimer, then you may not use, modify, or distribute this SNAPpy code.
# THE CODE IS PROVIDED UNDER THIS LICENSE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, WITHOUT LIMITATION, WARRANTIES THAT THE COVERED CODE IS FREE OF DEFECTS, MERCHANTABLE, FIT FOR A PARTICULAR PURPOSE OR NON-INFRINGING. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE COVERED CODE IS WITH YOU. SHOULD ANY COVERED CODE PROVE DEFECTIVE IN ANY RESPECT, YOU (NOT THE INITIAL DEVELOPER OR ANY OTHER CONTRIBUTOR) ASSUME THE COST OF ANY NECESSARY SERVICING, REPAIR OR CORRECTION. UNDER NO CIRCUMSTANCES WILL SYNAPSE BE LIABLE TO YOU, OR ANY OTHER PERSON OR ENTITY, FOR ANY LOSS OF USE, REVENUE OR PROFIT, LOST OR DAMAGED DATA, OR OTHER COMMERCIAL OR ECONOMIC LOSS OR FOR ANY DAMAGES WHATSOEVER RELATED TO YOUR USE OR RELIANCE UPON THE SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES OR IF SUCH DAMAGES ARE FORESEEABLE. THIS DISCLAIMER OF WARRANTY AND LIABILITY CONSTITUTES AN ESSENTIAL PART OF THIS LICENSE. NO USE OF ANY COVERED CODE IS AUTHORIZED HEREUNDER EXCEPT UNDER THIS DISCLAIMER.

"""
McastCounter.py ported to the SM700 EVB board
  Press the select-switch on any device to increment counter on all devices.
"""

secondCounter = 0
buttonCount = 0

BUTTON_PIN = 26 # SW1

LED1 = 23
LED2 = 24
LED3 = 25
LED4 = 1

def makeOutput(pin):
    setPinDir(pin, True)
    writePin(pin, False)

@setHook(HOOK_STARTUP)
def startupEvent():
    """This is hooked into the HOOK_STARTUP event"""
    global buttonState, buttonTime

    # Monitor for button-press events
    setPinDir(BUTTON_PIN, False)
    setPinPullup(BUTTON_PIN, True)
    monitorPin(BUTTON_PIN, True)
    setRate(3)

    # Initialize button-detect variables
    buttonState = readPin(BUTTON_PIN)
    buttonTime = getMs()

    makeOutput(LED1)
    makeOutput(LED2)
    makeOutput(LED3)
    makeOutput(LED4)

@setHook(HOOK_GPIN)
def buttonEvent(pinNum, isSet):
    """Hooked into the HOOK_GPIN event"""
    global buttonState, buttonTime, buttonCount
    if pinNum == BUTTON_PIN:
        buttonState = isSet
        if not isSet:
            buttonTime = getMs()
            incrementCount()

def incrementCount():
    """Button press action - increment and report new count"""
    global buttonCount
    buttonCount = buttonCount + 1
    buttonCount %= 100    # Wrap count at 99
    reportButtonCount()

def showButtonCount():
    if buttonCount & 1:
        pulsePin(LED1, 500, True)
    else:
        writePin(LED1, False)
    if buttonCount & 2:
        pulsePin(LED2, 500, True)
    else:
        writePin(LED2, False)
    if buttonCount & 4:
        pulsePin(LED3, 500, True)
    else:
        writePin(LED3, False)
    if buttonCount & 8:
        pulsePin(LED4, 500, True)
    else:
        writePin(LED4, False)

def doEverySecond():
    """Tasks that are executed every second"""
    showButtonCount()

@setHook(HOOK_100MS)
def timer100msEvent(currentMs):
    """Hooked into the HOOK_100MS event"""
    global secondCounter
    global buttonState,buttonTime,buttonCount

    secondCounter += 1
    if secondCounter >= 10:
        doEverySecond()
        secondCounter = 0

    # Use a LONG (> 1 second) button press as a "counter reset"
    if buttonState == False:
        if buttonCount > 0:
            if currentMs - buttonTime >= 1000:
                buttonCount = 0
                reportButtonCount()

def setButtonCount(newCount):
    """Set the new button count"""
    global buttonCount
    buttonCount = newCount
    showButtonCount()

def reportButtonCount():
    """Report to others that button press took place"""
    global buttonCount
    showButtonCount()
    mcastRpc(1,2,'setButtonCount',buttonCount)
