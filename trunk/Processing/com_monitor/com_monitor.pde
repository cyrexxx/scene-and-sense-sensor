/****************************************************************************
Title:    COM_MONITOR 
Author:   Kartik Karuna <kartik@kth.se>,Samarth Deo <samarthd@kth.se>
File:     $Id: COM_MONITOR ,v 2.0 2013/02/02 13:00:18 Kartik Exp $
Software:  Processing 1.5.1

Description:
    This Sketch listen to the Com port and parses the incoming data into an array.
    Relevant information is retrieved from this data is and stored in an Object.
    
Include Files (Libs)
     processing.serial
******************************************************************************/
import oscP5.*;
import netP5.*;
 
OscP5 oscP5;
NetAddress myRemoteLocation;
 

import processing.serial.*;
Serial myPort;                                    // The serial port
String inString;                                  // Input string from serial port
int lf = 10;                                      // ASCII linefeed 
String[] list;
int flag;
int count=0;

//Class for sending the packet. 
public class Packet{
    public int devNo;
   public int sensVal[]= new int[8];
}

Packet p = new Packet();
void setup() {
  size(400,400);
   
    println(Serial.list());                                             //Prints the available ports to chose from 
    myPort = new Serial(this, Serial.list()[0], 115200);                // Selects the port number here
    myPort.bufferUntil(lf); 
  
  // start oscP5, telling it to listen for incoming messages at port 12000 */
  oscP5 = new OscP5(this,12000);
 
  // set the remote location to be the localhost on port 57120
  myRemoteLocation = new NetAddress("127.0.0.1",57120);
}
 
void draw()
{
  if( flag ==1) 
  { 
    count++;
   //text("packets sent= " + count, 20,20*count); 
  sendData();
  flag =0;
  }
}

void serialEvent(Serial ser) 
{ int k=0;
    
    inString = ser.readString();

  // Splitting a String based on a multiple delimiters
    list = splitTokens(inString, "$,");
    flag=0;
    for (int i = 0; i < list.length-1; i++) 
      { 
        if(int(list[1])<8)            // The second element is the device address, a 1 bit integer number. In case address is more than 8 we ignore this packet as garbage.
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
                p.sensVal[k] = int(list[i]);         //This is an object where we want to store the data of the 8 sensors. There tags are not important. So every second element is what we need, leaving the sensor no.
                //println(p.sensVal[k]);
                //println("i=");
                //println(i);
                k++;
               }    
             }
         }
      }
  // ----v--------v--------v--------v--------v--------v----

flag=1; 
//sendData();
 
  // ----^--------^--------^--------^--------^--------^----
}

 void sendData()
{
//println("sent called");
OscMessage myMessage = new OscMessage("/Data");
 
  myMessage.add(p.sensVal); // add an int to the osc message
  myMessage.add(p.sensVal[1]); // add a float to the osc message 
  myMessage.add(p.sensVal[2]); // add a string to the osc message
 
  // send the message
  oscP5.send(myMessage, myRemoteLocation);
  //oscP5.flush(myMessage, myRemoteLocation);

 

}

/*
void mousePressed() {  
   create an osc message
 println("mouse press");
  
   
}
 */

void oscEvent(OscMessage theOscMessage) 
{  
  // get the first value as an integer
  int firstValue = theOscMessage.get(0).intValue();
 
  // get the second value as a float  
  int secondValue = theOscMessage.get(1).intValue();
 
  // get the third value as a string
  int thirdValue = theOscMessage.get(2).intValue();
 
  // print out the message
  print("OSC Message Recieved: ");
  print(theOscMessage.addrPattern() + " ");
  println(firstValue + " " + secondValue + " " + thirdValue);
}

