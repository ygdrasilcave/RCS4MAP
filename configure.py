import json

with open("settings.json") as json_file:    
	data = json.load(json_file)

TG_TOKEN = data["TELEGRAM"]["TOKEN"].strip()
TG_MASTER_ID = data["TELEGRAM"]["MASTER_ID"]

MOSQUITTO_IP = data["MOSQUITTO"]["IP"].strip()
MOSQUITTO_PORT = data["MOSQUITTO"]["PORT"]
MOSQUITTO_USER_NAME = data["MOSQUITTO"]["USER_NAME"].strip()
MOSQUITTO_PASSWORD = data["MOSQUITTO"]["PASSWORD"].strip()

OSC_SERVER_IP = data["OSC"]["SERVER_IP"].strip()
OSC_SERVER_PORT = data["OSC"]["SERVER_PORT"]
OSC_SERVER = (OSC_SERVER_IP, OSC_SERVER_PORT)
OSC_CLIENTS_IP = data["OSC"]["CLIENTS_IP"]
OSC_CLIENTS_PORT = data["OSC"]["CLIENTS_PORT"]
OSC_CLIENTS = []
for i in range(len(OSC_CLIENTS_IP)):
	OSC_CLIENTS.append((OSC_CLIENTS_IP[i], OSC_CLIENTS_PORT[i]))

clients = data.get("CLIENTS")

def get_pub_sub(p=""):
	_mqtt = clients.get(p)
	_osc_addr = ''
	if p is "OSC":
		_osc_addr = data["OSC"]["ADDR_PATTERN"] + '/'
	pub = []
	pub_args_string = []
	pub_args = []
	sub = []
	for c in _mqtt:
		for i in range(len(_mqtt[c])):

			payload_set = _mqtt[c][i]["PAYLOAD"]["SET"]["RANGE"]
			l = len(payload_set)
			if l > 0:
				payload = ''
				validation = False
				for j in range(l):
					_type = type(payload_set[j])

					if (_type is list):
						l2 = len(payload_set[j])
						if(l2 == 2):
							payload = payload + '('
							for m in range(l2):
								if(m == l2-1):
									payload = payload + str(payload_set[j][m]) + ')'
								else:
									payload = payload + str(payload_set[j][m]) + ','
							validation = True
						else:
							print(p + ":SET:RANGE:[[int,int]] data type not understood")
					else:
						print(p + ":SET:RANGE:[[int,int]] data type not understood")

				if(validation == True):
					p = _osc_addr + c + '/' + _mqtt[c][i]["MODULE"] + '/SET'
					s = _osc_addr + c + '/' + _mqtt[c][i]["MODULE"] + '/SET_ACK'
					pub.append(p.strip())
					sub.append(s.strip())
					pub_args_string.append(payload.strip())
					pub_args.append(payload_set)

			payload_get = _mqtt[c][i]["PAYLOAD"]["GET"]["VALUE"]
			l = len(payload_get)
			if l == 1:
				payload = ''
				for j in range(l):
					_type = type(payload_get[j])

					if (_type is str or _type is unicode):
						if (j == l-1):
							payload = payload + payload_get[j]
						else:
							payload = payload + payload_get[j] + ','
					else:
						print(p + ":GET:VALUE:[string] data type not understood")

				p = _osc_addr + c + '/' + _mqtt[c][i]["MODULE"] + '/GET'
				s = _osc_addr + c + '/' + _mqtt[c][i]["MODULE"] + '/GET_VAL'
				pub.append(p.strip())
				sub.append(s.strip())
				pub_args_string.append(payload.strip())
				pub_args.append(payload.strip())

	return pub, pub_args_string, pub_args, sub

mqtts = get_pub_sub("MQTT")
mqtt_publisher = mqtts[0]
mqtt_publisher_args_string = mqtts[1]
mqtt_publisher_args_list = mqtts[2]
mqtt_subscriber = mqtts[3]
oscs = get_pub_sub("OSC")
osc_publisher = oscs[0]
osc_publisher_args_string = oscs[1]
osc_publisher_args_list = oscs[2]
osc_subscriber = oscs[3]

sched = data["SCHEDULED"]["MODULE"]
SCHEDULED = []
SCHEDULED_TIME = data["SCHEDULED"]["TIME"]
SCHED_MSG = 'SCHEDULED MODULES\n' + SCHEDULED_TIME[0]+' '+SCHEDULED_TIME[1]+' '+SCHEDULED_TIME[2] + '\n'
for s in sched:
	isGet = s.split('/')
	if(isGet[len(isGet)-1] == 'GET'):
		if(s in mqtt_publisher):
			index = mqtt_publisher.index(s)
			arg = mqtt_publisher_args_list[index]
			ma = [s, arg]
			SCHEDULED.append(ma)
			SCHED_MSG = SCHED_MSG + s + '\n'
		elif(s in osc_publisher):
			index = osc_publisher.index(s)
			arg = osc_publisher_args_list[index]
			ma = [s, arg]
			SCHEDULED.append(ma)
			SCHED_MSG = SCHED_MSG + s + '\n'
		else:
			print(s + ' is not in the Publisher')
	else:
		print('SCHEDULED MODULE is available for "GET" method')


f = open("RCS4MAP_ref.tsv", 'w')

line = 'SCHEDULED_TIME:'+'	'+SCHEDULED_TIME[0]+'	'+SCHEDULED_TIME[1]+'	'+SCHEDULED_TIME[2] + '\n\n' 
f.write(line)
line = 'MQTTT PUBLISHER'+'	'+'ARGS'+'	'+'SUBSCRIBER'+'	'+'SCHEDULED\n'
f.write(line)
for i in range(len(mqtt_publisher)):
	sched = 'N/A'
	mod = mqtt_publisher[i]
	for m in SCHEDULED:
		if(mod == m[0]):
			sched = 'SCHEDULED'
	line = mod + '	' + mqtt_publisher_args_string[i]  + '	' + mqtt_subscriber[i] + '	' + sched + '\n'
	f.write(line)
f.write('\n')

line = 'OSC PUBLISHER'+'	'+'ARGS'+'	'+'SUBSCRIBER'+'	'+'SCHEDULED\n'
f.write(line)
for i in range(len(osc_publisher)):
	sched = 'N/A'
	mod = osc_publisher[i]
	for m in SCHEDULED:
		if(mod == m[0]):
			sched = 'SCHEDULED'
	line = mod + '	' + osc_publisher_args_string[i]  + '	' + osc_subscriber[i] + '	' + sched + '\n'
	f.write(line)
f.close()

def printConf():
	print("___ MQTT PUBLISHER ___")
	for m in mqtt_publisher:
		print(m)

	print("___ MQTT PUBLISHER ARGS STRING ___")
	for m in mqtt_publisher_args_string:
		print(m)

	print("___ MQTT PUBLISHER ARGS LIST ___")
	for m in mqtt_publisher_args_list:
		print(m)

	print("___ MQTT SUBSCRIBER ___")
	for m in mqtt_subscriber:
		print(m)

	print("___ OSC PUBLISHER ___")
	print(osc_publisher)
	for m in osc_publisher:
		print(m)

	print("___ OSC PUBLISHER ARGS STRING ___")
	print(osc_publisher_args_string)
	for m in osc_publisher_args_string:
		print(m)

	print("___ OSC PUBLISHER ARGS LIST ___")
	print(osc_publisher_args_list)
	for m in osc_publisher_args_list:
		print(m)

	print("___ OSC SUBSCRIBER ___")
	for m in osc_subscriber:
		print(m)
		
	print("___ SCHEDULED ___")
	for m in SCHEDULED:
		print(m)
