# run fisch_serial.py in Python, needs pygamezero
# before start: check COM port
# after start: type amplitude of force that you expect or aim at and move window for its best visibility
# reading and logging of serial port starts with run
# press -> to start fish and bubbles and logging of trigger
# press <- to pause fish and bubbles and logging of trigger
# press arrow up to redraw bubbles
# press t to send reset_tare signal to green box

import pgzrun
import serial
from threading import Thread
from datetime import datetime
import time
import sys
import glob
import math
import random

ser = None  # will stay None in simulation mode
simulate_force = False

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
        #ports = glob.glob('/dev/pts/2')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

ports = serial_ports()

#port=input("Type port [" + ", ".join(ports) + "]: ")
choice = input("Type port [" + ", ".join(ports) + "] or 'sim' for simulation: ")
if choice.strip().lower() == "sim":
         simulate_force=True
else:
    ser = serial.Serial(choice, baudrate = 9600, timeout = 0.5)
    ser.flushInput()

sollwert=int(input("Expected force amplitude? "))  #sollwert=30 is top value from arduino, sollwert from force sensor is 10% of max. vol. force
WIDTH=800
HEIGHT=600
TITLE="Der Fisch"
FISHBASELINE=450
fish= Actor("fish3")
fish.pos=80,FISHBASELINE

bubble_list=[]
blasenzahl=50
sollkurve_list=[0,0,1 , 1 ,2 ,5 ,12 ,23,38 ,50 ,56 ,58,60,61 ,61 ,62,62,61,61,60,59,57,54 ,49,42 ,35 , 28,22,16 ,12 ,9 ,6, 5 ,3 ,2,1 ,1,0,0 ,0,0,0,1,0, 0,0 ,0 ,0,0 ,0 ,0 ]
topforce=300


game_pause=True
score=0
decoded_bytes=0
logName=('ForceLog' + time.strftime("_%Y-%m-%d_%H.%M.%S.csv"))
lastReset = 0


def create_bubble():                    #function to create initial bubble curve and refreshed bubble curve
    global bubble_list, FISHBASELINE, topforce
    bubble_list=[]
    x=0
    for y in sollkurve_list:
        bubble_new=Actor("bubble2")
        bubble_new.pos=(WIDTH-(int(x*WIDTH/blasenzahl)),FISHBASELINE-(int(y/62*topforce)))
        bubble_list.append(bubble_new)
        x=x+1
    return

    
def worker():    #serial connection, reading from it as a thread
    global decoded_bytes
    t0=time.time()
    while True:
        #simulate data mode
        if simulate_force:
            elapsedtime= time.time() -t0
            decoded_bytes = abs(math.sin(elapsedtime)) * sollwert
            time.sleep(0.05)
            continue
        
        # real serial mode
        
##        print(data)
        try:
            data = ser.readline()
            decoded_bytes = float(data[7:len(data)-2].decode("utf-8"))
        
##            print(decoded_bytes)
            with open(logName, 'a') as File:        #log file, writes 10 lines per second
                timestamp = time.time()
                File.write(datetime.now().strftime('%d-%m-%Y-%H-%M-%S')+','+str(timestamp)+','+' Force in N: , '+str(decoded_bytes)+ '\n')
            

        except:
            print(data)
            continue

t = Thread(target=worker)
t.daemon = True
t.start()

create_bubble()         #create initial bubble curve

def draw():
    screen.blit("reef",(0,0))
    if not game_pause:
        for bubble in bubble_list:
            bubble.draw()
        screen.draw.text("Punkte: "+str(score),(680,5),color="black")
        fish.draw()
    return


def send_trigger():
    global ser
    if simulate_force or ser is None:
        print("sim mode, no trigger send")
    else:
        try:
            ser.write(b'TRIG\n')
        except Exception as e:
            print("Failed to send TRIG:", e)

    # allways log trigger, sim or real 
    with open(logName, 'a') as File:    #write trig signal to log file
        timestamp = time.time()
        File.write(datetime.now().strftime('%d-%m-%Y-%H-%M-%S')+','+str(timestamp)+','+'Trig'+'\n')
    return

def resetTare():
    global lastReset, ser
    if time.time() - lastReset <= 5: return
    lastReset = time.time()
    if simulate_force or ser is None:
        print("sim mode, no reset")
    else:    
        ser.write(b'RESET\n')    #reset tare signal for green box, needs new line command
    return


def update(dt):             #update every dt seconds, approx 1/60
    global game_pause, score, bubble_list, decoded_bytes, topforce, sollwert, FISHBASELINE, ser #ser
    if keyboard.right and game_pause==True:  #press -> to start
        game_pause=False
    if keyboard.left and game_pause==False:  #press <- to pause
        game_pause=True
    if keyboard.up:                         #press "up" to refresh and redraw bubble curve
        create_bubble()
    if keyboard.t:
        resetTare()
    if keyboard.p:
        sollwert -= 0.1
        print(sollwert)
    if keyboard.m:
        sollwert += 0.1
        print(sollwert)

    if sollwert <= 0: sollwert = 1
    
    if not game_pause:

        if bubble_list[2].x<=0:     #adapt timing for trigger signal by changing the default "5" to other number (at 2 it starts earlier, at 10 later)
            send_trigger()
        for bubble in bubble_list:
            if (bubble.colliderect(fish)) and bubble.image==("bubble2"):
                bubble.image=("empty")
                score += 1
            if bubble.x>0:
                bubble.x -= WIDTH/4*dt      #move WIDTH/4 pixels per second, ie cycle=4 s
            else:
                bubble.image=("bubble2")
                bubble.x=WIDTH
             
        fish.y = FISHBASELINE - int(decoded_bytes/sollwert*topforce)    #sollwert=30 is top value from arduino, sollwert from force sensor is 10% of max. vol. force, it will be normalize it to topforce

##        with open(logName, 'a') as File:                        #optional position for logging block: log file, writes 60 lines per second in update loop!!!
##            timestamp = time.time()
##            File.write(datetime.now().strftime('%d-%m-%Y-%H-%M-%S')+','+str(timestamp)+','+' Force in N: , '+str(decoded_bytes)+ '\n')


          

pgzrun.go()
