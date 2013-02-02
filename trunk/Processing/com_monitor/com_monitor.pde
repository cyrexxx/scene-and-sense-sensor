/****************************************************************************
Title:    COM_MONITOR 
Author:   Kartik Karuna <kartik@kth.se>,Samarth Deo <samarthd@kth.se>
File:     $Id: COM_MONITOR ,v 1.0 2013/02/02 13:00:18 Kartik Exp $
Software:  Processing 1.5.1

Description:
    This Sketch listen to the Com port and parse the incoming data into an array
    relevant information is retrieved from this data is and stored in Object.
    
Include Files (Libs)
     processing.serial
******************************************************************************/

import processing.serial.*;
Serial myPort; // The serial port
String inString; // Input string from serial port
int lf = 10; // ASCII linefeed 
String[] list;

//Class for sending the packet. 
public class Packet{
    public int devNo;
   public int sensVal[]= new int[20];
}

// Listing the serial ports from here. This is where you pick up the 
// COM port number form the lsit displayed on running. We set the baud
// rate here too which is currently 115200
void setup() 
{ 
    size(800,100); 
    println(Serial.list());
    myPort = new Serial(this, Serial.list()[0], 115200); 
    myPort.bufferUntil(lf); 
}
//Just a window to check the data recieved, can be removed later.
void draw() 
{ 
    background(0); 
    for (int i = 0; i < 50; i++) 
    text("received: " + inString, 10,50); 
}
// The main function which reads and parses the string recieved to an 
// array of integers. The first value of array is an garbage.
void serialEvent(Serial ser) 
{ int k=0;
    Packet p = new Packet();
    inString = ser.readString(); 
// Splitting a String based on a multiple delimiters
    list = splitTokens(inString, "$,");
for (int i = 0; i < list.length-1; i++) 
{ 
  if(int(list[1])<8)            // The second element is the device address, a 1 bit integer number. In case address is more than 8
                                  // we ignore this packet as garbage.
 {
  if (i ==1)
  {
   p.devNo = int(list[1]);                     // This is where you get the device number and we are trying to store in an object.
    //println(p.devNo);
  } 
  if (i>1)
   {
     if (i % 2 !=0)
   
    {
           p.sensVal[k] = int(list[i]);         //This is an object where we want to store the data of the 8 sensors. There tags
                                                  // are not important. So every second element is what we need, leaving the sensor no.
           //println(p.sensVal[k]);
           //println("i=");
           //println(i);
           k++;
         }
   
   }

   }
}
}
