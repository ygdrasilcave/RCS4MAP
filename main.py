import configure
import oled
import telepot
from telepot.loop import MessageLoop
#import telepot.api
import paho.mqtt.client as mqtt
import OSC
import time
import threading
import os.path
from os import path
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
"""
import logging
log = logging.getLogger('apscheduler.executors.default')
log.setLevel(logging.INFO)  # DEBUG
fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
h = logging.StreamHandler()
h.setFormatter(fmt)
log.addHandler(h)
"""
#telepot.api._pools = {
#	'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=6, timeout=30),
#}
auth = configure.TG_TOKEN
masterId = configure.TG_MASTER_ID
bot = telepot.Bot(auth)

mqtt_client = mqtt.Client(configure.MOSQUITTO_USER_NAME + '/000') 
mqtt_client.username_pw_set(username=configure.MOSQUITTO_USER_NAME, password=configure.MOSQUITTO_PASSWORD)
#mqtt_client.connect_async(host=configure.MOSQUITTO_IP, port=configure.MOSQUITTO_PORT, keepalive=60) 
mqtt_client.connect(host=configure.MOSQUITTO_IP, port=configure.MOSQUITTO_PORT, keepalive=60) 

osc_server = OSC.OSCServer(configure.OSC_SERVER)
osc_client = []

oled_new_message = False
oled_new_message_prev = oled_new_message
oled_msg = ['','']

#sched = BackgroundScheduler(daemon=True)
sched = BackgroundScheduler()
sched_day_of_week = configure.SCHEDULED_TIME[0]   	# 0-6 mon,tue,wed,thu,fri,sat,sun
sched_hour = configure.SCHEDULED_TIME[1]             # 0-23
sched_minute = configure.SCHEDULED_TIME[2]           # 0-59

#configure.printConf()

new_osc_msg = False
msg_tg = ''

# MQTT ########################################################################################
#0: connection succesful
#1: connection refused - incorect protocol version
#2: connection refused - ivalid client identifier
#3: connection refused - server unavailable
#4: connection refused - bad username or password
#5: connection refused - not authorised
def mqtt_on_connect(client, userdata, flags, rc):
	if rc==0:
		print("MQTT: Connected OK Returned code=" + str(rc))
		sub = configure.mqtt_subscriber
		n = len(sub)
		if(n > 0):
			print('***** Subscriber *****')
			for i in range(n):
				sn = sub[i]
				mqtt_client.subscribe(sn)
				print(sn)
			print('*********************')
	else:
		print("MQTT: Bad connection Returned code=" + str(rc))

def mqtt_on_message(client, userdata, msg):
	if(msg.topic in configure.mqtt_subscriber):
		if(msg.topic == '002/image/GET_VAL'):
			fn = '/home/pi/RCS4MAP/imgs/' + msg.payload
			print("..... send photo ..... " + fn)
			tg_send_image(auth, fn, masterId)			
		else:
			m = msg.topic + ' ' + msg.payload
			bot.sendMessage(masterId, m)
		print('<===== SUB: ' + m)
	else:
		print(msg.topic + ' ' + msg.payload)
	###print(str(msg.topic) + ' ' + str(msg.payload.decode("utf-8")))

#def mqtt_on_subscribe(client, userdata, mid, granted_qos):
#	print("subscribed: " + str(mid) + " " + str(granted_qos))

def mqtt_send(_topic, _payload):
	mqtt_client.publish(_topic, _payload)
	print('=====> PUB: ' + _topic + ' ' + _payload)

def mqtt_on_disconnect(client, userdata, flags, rc=0):
	print('MQTT Diconnected')
	print(str(rc))

# OSC ###########################################################################################
def osc_close():
	print('===== Waiting for OSC server-thread to finish =====')
	for i in range(len(osc_client)):
		osc_client[i].close()
	osc_server.close()
	print('===== Done =====')

def osc_send_msg(client, addr, msg):
	bundle = OSC.OSCBundle()
	bundle.append( {'addr':addr, 'args':msg} )
	client.send(bundle)
	print('-----> OSC out: ' + addr + ' ' + msg)

def osc_parse(addr, tags, stuff, source):
	global new_osc_msg, msg_tg
	print('<----- OSC in: ')
	print("	received new OSC msg from %s" % OSC.getUrlStr(source))
	print("	with addr : %s" % addr)
	print("	typetags %s" % tags)
	print("	data %s" % stuff)
	print("	---")
	if addr in configure.osc_subscriber:
		print('address pattern: pass')
		if(tags == 's'):
			print('typetag: pass')
			#m = addr + ' ' + stuff[0].strip()
			#bot.sendMessage(masterId, m)
			new_osc_msg = True
			msg_tg = addr + ' ' + stuff[0].strip()
			#print('Sent Bot message')

def osc_init():
	i = 0
	for c in configure.OSC_CLIENTS:
		osc_client.append(OSC.OSCClient())
		osc_client[i].connect(c)
		i = i+1
	print('===== OSC Clients connected =====')
	print(osc_client)
	print('=================================')
	#oscServer.addDefaultHandlers()
	for addr in configure.osc_subscriber:
		osc_server.addMsgHandler(addr, osc_parse)
	print('===== OSC Server handlers =====')
	for addr in osc_server.getOSCAddressSpace():
		print(addr)
	print('===============================')

# Telegram ########################################################################################
def tg_system_info():
	#raspberry pi 3
	with open("/sys/class/thermal/thermal_zone0/temp") as f:
	#raspberry pi 2, banana pi
	#with open("/sys/devices/platform/sunxi-i2c.0/i2c-0/0-0034/temp1_input") as f:
		temp = str(int(f.read())/1000)

	statvfs = os.statvfs('/')
	totalSize = str((statvfs.f_frsize * statvfs.f_blocks)/1000000)
	freeSize = str((statvfs.f_frsize * statvfs.f_bavail)/1000000)
	info = 'sys temperature: ' +temp+ 'C\ntotalSize: ' + totalSize + 'M\nfreeSize: ' + freeSize + 'M' 
	bot.sendMessage(masterId, info)

def tg_help():
	lm = len(configure.mqtt_publisher)
	if(lm == len(configure.mqtt_publisher_args_string)): 
		print('----- MQTT Modules -----')
		for i in range(lm):
			help_msg = '!' + configure.mqtt_publisher[i] + ' ' + configure.mqtt_publisher_args_string[i]
			bot.sendMessage(masterId, help_msg)
			print(help_msg)
		print('-----------------------')
	lo = len(configure.osc_publisher)
	if(lo == len(configure.osc_publisher_args_string)):
		print('----- OSC Modules -----') 
		for i in range(lo):
			help_msg = '!' + configure.osc_publisher[i] + ' ' + configure.osc_publisher_args_string[i]
			bot.sendMessage(masterId, help_msg)
			print(help_msg)
		print('----------------------')

def _isDigit(f):
    try:
        float(f)
        return True
    except ValueError:
        return False

def _parse(mod, publisher, arg_list, cmd):
	global oled_new_message, oled_new_message_prev, oled_msg
	_isFunc = False
	if(mod in publisher):
		index = publisher.index(mod)
		arg = arg_list[index]
		arg_type = type(arg)
		sg = ''
		type_of_mod = ''
		if(mod[0] == '/'): 	#OSC
			sg = mod.split('/')[4]
			type_of_mod = 'OSC'
		else:				#MQTT
			sg = mod.split('/')[2]
			type_of_mod = 'MQTT'
		if(sg == 'SET'):
			if(arg_type is list):
				arg_length = len(arg)
				input_val = cmd.split(',')
				input_val_length = len(input_val)
				validation = 0
				if(arg_length == input_val_length):
					for i in range(arg_length):
						#if(input_val[i].isdigit() == True):
						if(_isDigit(input_val[i]) == True):
							arg_min = arg[i][0]
							arg_max = arg[i][1]
							arg_get = float(input_val[i])
							if(arg_get >= arg_min and arg_get <= arg_max):
								validation = validation + 1
							else:
								print('SET RANGE is invalid: out of range')
						else:
							print('SET RANGE is invalid: input value was not a number')
				else:
					print('SET RANGE is invalid: ' + str(arg_length) + ' value(s) expected, ' + str(input_val_length) + ' value(s) are given')

				if(validation == arg_length):
					if(type_of_mod == 'OSC'):
						for i in range(len(osc_client)):
							osc_send_msg(osc_client[i], mod, cmd)
					elif(type_of_mod == 'MQTT'):
						mqtt_send(mod, cmd)
					_isFunc = True
					oled_new_message_prev = oled_new_message
					oled_new_message = True
					oled_msg = [mod, cmd]
				else:
					_isFunc = False

		elif(sg == 'GET'):
			if(arg_type is str or arg_type is unicode):
				if(cmd == arg):
					if(type_of_mod == 'OSC'):
						for i in range(len(osc_client)):
							osc_send_msg(osc_client[i], mod, cmd)
					elif(type_of_mod == 'MQTT'):
						mqtt_send(mod, cmd)
					_isFunc = True
					oled_new_message_prev = oled_new_message
					oled_new_message = True
					oled_msg = [mod, cmd]
				else:
					_isFunc = False
					print('GET VALUE is invalid')
	return _isFunc

def tg_parse_message(msg):
	content_type, chat_type, chat_id = telepot.glance(msg)
	if((content_type == 'text') and (chat_type =='private') and (chat_id == masterId)):
		cmd = msg['text'].strip().split(' ')	
		isFunc = False
		if len(cmd) == 2:
			if(cmd[0][0] == '!'):
				module = cmd[0][1:]
				p = _parse(module, configure.mqtt_publisher, configure.mqtt_publisher_args_list, cmd[1])
				if(p == False):
					p = _parse(module, configure.osc_publisher, configure.osc_publisher_args_list, cmd[1])
				isFunc = p
		elif len(cmd) == 1:
			if (cmd[0][0] == '!') and (cmd[0][1:] == 'help'):
				tg_help()
				isFunc = True
			elif (cmd[0][0] == '!') and (cmd[0][1:] == 'sys'):
				tg_system_info()
				isFunc = True
			else:
				isFunc = False

		if (isFunc == False):
			bot.sendMessage(masterId, 'Wrong command!')
	else:
		tg_echo(msg)

def tg_echo(_msg):
	content_type, chat_type, chat_id = telepot.glance(_msg)
	reply = ''
	#chat_type: private, group
	if chat_id < 0:
		# group message
		reply += 'G: Received a %s from %s' % (content_type, str(chat_id))
		reply += '\n'
		#print 'Received a %s from %s' % (content_type, str(chat_id))
	else:
		# private message
		reply += 'P: Received a %s from %s' % (content_type, str(chat_id))
		reply += '\n'
		#print 'Received a %s from %s' % (content_type, str(chat_id))

	if content_type == 'text':
		reply += _msg['text'].strip()
	bot.sendMessage(masterId, reply)
	bot.sendMessage(chat_id, "Sorry, this is a private Bot")

def tg_send_image(botToken, imageFile, chat_id):
	command = 'curl -k -F chat_id='+str(chat_id)+' -F photo=@"'+ imageFile +'" https://api.telegram.org/bot'+botToken+'/sendPhoto'
	subprocess.call(command.split(' '))
	#process = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE)
	#output = process.communicate()[0]
	#print(output)
	return
#################################################################################################
#tg_help();
#bot.message_loop(tg_parse_message)
MessageLoop(bot, tg_parse_message).run_as_thread()

mqtt_client.on_connect = mqtt_on_connect 
mqtt_client.on_disconnect = mqtt_on_disconnect
#mqtt_client.on_subscribe = mqtt_on_subscribe
mqtt_client.on_message = mqtt_on_message
mqtt_client.loop_start()

osc_init()
osc_serverThread = threading.Thread(target = osc_server.serve_forever)
#osc_serverThread.daemon = True
osc_serverThread.start()

def restart():
	command = "/usr/bin/sudo /sbin/shutdown -r now"
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
	output = process.communicate()[0]
	print(output)

oled_update_time = int(time.time() * 1000)
oled_update_time_interval = 500
oled_msg_time = 0
oled_msg_time_interval = 5000

bot.sendMessage(masterId, '<<<<< MAPCS: started >>>>>')
bot.sendMessage(masterId, configure.SCHED_MSG)

@sched.scheduled_job('cron', day_of_week=sched_day_of_week, hour=sched_hour, minute=sched_minute)
def sched_report():
	sm = configure.SCHEDULED
	for m in sm:
		if(m[0] in configure.mqtt_publisher):
			mqtt_send(m[0], m[1])
		elif(m[0] in configure.osc_publisher):
			for i in range(len(osc_client)):
				osc_send_msg(osc_client[i], m[0], m[1])
	print('scheduled time: request')

if(len(configure.SCHEDULED)>0):
	sched.start()
	print('~~~ scheduled modules ~~~')
	print(configure.SCHEDULED)
	print('~~~~~~~~~~~~~~~~~~~~~~~~~')

def loop():
	global oled_update_time, oled_msg_time, oled_new_message, oled_new_message_prev, new_osc_msg

	current_time = int(time.time() * 1000)

	if(oled_new_message_prev==False and oled_new_message==True):
		oled_msg_time = current_time
		oled_new_message_prev = oled_new_message
	
	if(oled_new_message == True):
		oled.oled_printMsg(oled_msg)
		if(current_time > oled_msg_time + oled_msg_time_interval):
			oled_new_message = False
			oled_new_message_prev = oled_new_message
	else:
		if(current_time > oled_update_time + oled_update_time_interval):
			oled.oled_system()
			oled_update_time = current_time

	if(new_osc_msg == True):
		bot.sendMessage(masterId, msg_tg)
		print('Sent Bot message')
		new_osc_msg = False
		print(new_osc_msg)

if __name__ == '__main__':
    try:
        print('<<<<< MAPCS >>>>>')
        print('Press Ctrl-C to quit.')
        while True:
            loop()
    finally:
    	oled.oled_clear()
    	time.sleep(1)
    	osc_close()
    	time.sleep(1)
    	mqtt_client.disconnect()
    	time.sleep(1)
    	osc_serverThread.join()
    	time.sleep(1)
    	sched.shutdown()
    	print("exit")
