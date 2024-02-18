from machine import Pin, SPI
import time
import network
from umqtt.robust import MQTTClient
import ujson
import dht
from machine import Timer
import utime
from ili934xnew import ILI9341, color565
from micropython import const
import os
import glcdfont
import tt14
import tt24
import tt32
import time
import re

# Dimenzije displeja
SCR_WIDTH = const(320)
SCR_HEIGHT = const(240)
SCR_ROT = const(2)
CENTER_Y = int(SCR_WIDTH/2)
CENTER_X = int(SCR_HEIGHT/2)

print(os.uname())

# Podešenja SPI komunikacije sa displejem
TFT_CLK_PIN = const(18)
TFT_MOSI_PIN = const(19)
TFT_MISO_PIN = const(16)
TFT_CS_PIN = const(17)
TFT_RST_PIN = const(20)
TFT_DC_PIN = const(15)

spi = SPI(
    0,
    baudrate=62500000,
    miso=Pin(TFT_MISO_PIN),
    mosi=Pin(TFT_MOSI_PIN),
    sck=Pin(TFT_CLK_PIN))

print(spi)

display = ILI9341(
    spi,
    cs=Pin(TFT_CS_PIN),
    dc=Pin(TFT_DC_PIN),
    rst=Pin(TFT_RST_PIN),
    w=SCR_WIDTH,
    h=SCR_HEIGHT,
    r=SCR_ROT)

sensor = dht.DHT11(Pin(28))

keyMatrix = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]
colPins = [0, 1, 2, 3]
rowPins = [21, 22, 26, 27]

row = []
column = []

# Uspostavljanje WiFI konekcije
nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect('Redmi princeza', 'kokakola') #ukucati naziv i password

while not nic.isconnected():
    print("Čekam konekciju ...")
    time.sleep(5)

print("WLAN konekcija uspostavljena")
ipaddr=nic.ifconfig()[0]

print("Mrežne postavke:")
print(nic.ifconfig())

pom = 'C'
provjera = None
# Funkcija koja se izvršava na prijem MQTT poruke
def change_displej(topic,msg):
    p = str(msg)
    global provjera
    provjera = p[2]
    print(provjera)
    msg = '{{"Tipka se promijenila na": {}}} ' .format(provjera)
    mqtt_conn.publish(b'tele/dreamTeam/SENZOR',msg)
    
cifra = 0
def fja_senzor():
    time.sleep(2)
    sensor.measure()
    global temp
    temp = sensor.temperature()
    tempera = temp
    msg = str(tempera)
    mqtt_conn.publish(b'tele/dreamTeam/SENZOR',msg)

for item in rowPins:
    row.append(machine.Pin(item,machine.Pin.OUT))
for item in colPins:
    column.append(machine.Pin(item,machine.Pin.IN,machine.Pin.PULL_DOWN))
key = '0'
def scanKeypad():
    global key
    for rowKey in range(4):
        row[rowKey].value(1)
        for colKey in range(4):
            if column[colKey].value() == 1:
                key = keyMatrix[rowKey][colKey]
                row[rowKey].value(0)
                return(key)
        row[rowKey].value(0)
       
def sendKey():
    key = scanKeypad()
    if str(key) != 'None':
        if str(key) == 'A' or str(key) == 'B':
            print("Key pressed is:{}".format(key))
            tipka = str(key)
            poruka = tipka
            mqtt_conn.publish(b'displej/onoff',poruka)
        else:
            prvacifra = int(key);
            tipka = str(prvacifra)
            poruka = '{{"Prva cifra": {} }} ' .format(tipka)
            mqtt_conn.publish(b'tele/dreamTeam/tipke', poruka)
            time.sleep(3);
            key = scanKeypad()
            drugacifra = int(key);
            global cifra
            cifra = prvacifra*10+drugacifra;
            slanje = str(cifra)
            poruka = cifra
            mqtt_conn.publish(b'zeljenatemperatura', slanje)
            
def displej():
    display.erase()
    display.set_pos(0,0)
    display.set_font(tt24)
    display.set_color(color565(255,255,0), color565(150,150,150))
    if str(provjera) == 'A':
        display.print("\nMjerena temperatura sobe je: {}".format(temp))
        display.print("\nZeljena temperatura sobe je: {}".format(cifra))
    elif str(provjera) == 'B':
        display.print("\nGrijanje je isključeno")
    

# Uspostavljanje konekcije sa MQTT brokerom
mqtt_conn = MQTTClient(client_id='unikat', server='broker.hivemq.com',user='',password='',port=1883)
mqtt_conn.connect()
mqtt_conn.set_callback(change_displej)
mqtt_conn.subscribe(b"displej/onoff")


print("Konekcija sa MQTT brokerom uspostavljena")


# U glavnoj petlji se čeka prijem MQTT poruke

brojac = 0
while True:
    mqtt_conn.check_msg()
    sendKey()
    fja_senzor()
    displej()
    print(provjera)

