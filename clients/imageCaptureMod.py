import paramiko
from scp import SCPClient
import sys
import time
from picamera import PiCamera
from datetime import datetime
import os.path
from os import path
import paho.mqtt.client as mqtt

SERVER_IP = '192.168.1.142'
SERVER_USER_NAME = 'pi'
SERVER_PASSWORD = '*******'
MQTT_PORT = 1883
MQTT_MODULE_ID = '002'
MQTT_SUBSCRIBER = '002/image/GET'
MQTT_PUBLISHER = '002/image/GET_VAL'
MQTT_USER_NAME = 'MAPCS'
MQTT_PASSWORD = '1111'
img_local_dir = '/home/pi/imgs/'
img_remote_dir = '/home/pi/RCS4MAP/imgs'

camera = PiCamera()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(SERVER_IP, username=SERVER_USER_NAME, password=SERVER_PASSWORD)
ssh.exec_command('sudo')

imgName = ''
transmit = False
def progress(filename, size, sent):
	global transmit
	if(float(sent)/float(size)*100 == 100):
		transmit = True
		print("done")
scp = SCPClient(ssh.get_transport(), progress=progress)

def take_image_and_send():
	global imgName
	now = datetime.now().strftime("%Y%m%d_%H_%M_%S")
	imgName = now+'.jpg'
	imgPath = img_local_dir + imgName
	camera.start_preview()
	time.sleep(3)
	camera.capture(imgPath)
	camera.stop_preview()
	print('capture done')
	time.sleep(1)
	if(path.exists(imgPath) == True):
		print('sending... ' + now + '.jpg')
		scp.put(imgPath, recursive=True, remote_path=img_remote_dir)

def mqtt_on_connect(client, userdata, flags, rc):
	if rc==0:
		print("MQTT: Connected OK Returned code=" + str(rc))
		print('***** Subscriber *****')
		mqtt_client.subscribe(MQTT_SUBSCRIBER)
		print(MQTT_SUBSCRIBER)
		print('**********************')
	else:
		print("MQTT: Bad connection Returned code=" + str(rc))

def mqtt_on_message(client, userdata, msg): 
	if msg.payload == b'img':
		print('***** Subscribe ***** ' + msg.payload)
		take_image_and_send()
	else:
		pirnt(msg.topic + ' ' + msg.payload)

#def mqtt_on_subscribe(client, userdata, mid, granted_qos):
#	print("subscribed: " + str(mid) + " " + str(granted_qos))

def mqtt_send(_topic, _payload):
	mqtt_client.publish(_topic, _payload)
	print('***** Publish *****')
	print(_topic + ' ' + _payload)
	print('*******************')

def mqtt_on_disconnect(client, userdata, flags, rc=0):
	print('MQTT Diconnected')
	print(str(rc))

mqtt_client = mqtt.Client(MQTT_MODULE_ID) 
mqtt_client.username_pw_set(username=MQTT_USER_NAME, password=MQTT_PASSWORD)
mqtt_client.connect(host=SERVER_IP, port=MQTT_PORT, keepalive=60)
mqtt_client.on_connect = mqtt_on_connect 
mqtt_client.on_disconnect = mqtt_on_disconnect
#mqtt_client.on_subscribe = mqtt_on_subscribe
mqtt_client.on_message = mqtt_on_message
mqtt_client.loop_start()

def loop():
	global transmit, imgName
	if(transmit == True):
		mqtt_send(MQTT_PUBLISHER, imgName)
		transmit = False

if __name__ == '__main__':
    try:
        print 'Press Ctrl-C to quit.'
        while True:
            loop()
    finally:
    	scp.close()
    	mqtt_client.disconnect()
    	print("exit")