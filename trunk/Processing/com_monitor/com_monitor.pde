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
import processing.serial.*;

Serial myPort;     
OscP5 oscP5;
NetAddress myRemoteLocation;
String[] list;

void setup() {
  oscP5 = new OscP5(this, 12000);
  myRemoteLocation = new NetAddress("127.0.0.1", 57120);
  println(Serial.list());
  myPort = new Serial(this, Serial.list()[10], 115200);    
  myPort.bufferUntil('\n'); 
}

//void draw() {}

void serialEvent(Serial ser) {    
    String inString = ser.readString();
    list = splitTokens(inString, "$,");
    OscMessage myMessage = new OscMessage("/data");
    
      myMessage.add(float(list[1])/3000.0);
      myMessage.add(float(list[2])/3000.0);
      myMessage.add(float(list[3])/3000.0);
      myMessage.add(float(list[4])/3000.0);
      myMessage.add(float(list[5])/3000.0);
      myMessage.add(float(list[1])/3000.0);
      myMessage.add(float(list[2])/3000.0);
      myMessage.add(float(list[3])/3000.0);
      for (int i = 1; i < list.length-1; i++) {
      float val1 = float(list[i])/3000.0;
      println("Value of i = "+ i +" " + val1);
      }; 
    oscP5.send(myMessage, myRemoteLocation);
}
