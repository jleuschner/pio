#!/usr/bin/python
import time
import RPIO as GPIO
from Adafruit_PWM_Servo_Driver import PWM
import SocketServer
import json

PROMPT="PIO02>"
HOST = ''
PORT = 2000

# Pinning - Out
LED_RED = 8
LED_GRN = 7
#RELAY1 = 18
#RELAY2 = 23
#RELAY3 = 24
#RELAY4 = 25
RELAYS = [18,23,24,25]
# Pinning - Out
SWITCH_PWR = 9
SWITCH_RST = 10

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # GPIO.BOARD fuer Pin-Nummerierung

GPIO.setup(LED_RED,GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LED_GRN,GPIO.OUT, initial=GPIO.HIGH)
for i in RELAYS:
	GPIO.setup(i,GPIO.OUT, initial=GPIO.HIGH)
	
#GPIO.setup(RELAY1,GPIO.OUT, initial=GPIO.HIGH)
#GPIO.setup(RELAY2,GPIO.OUT, initial=GPIO.HIGH)
#GPIO.setup(RELAY3,GPIO.OUT, initial=GPIO.HIGH)
#GPIO.setup(RELAY4,GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(SWITCH_PWR,GPIO.IN)
GPIO.setup(SWITCH_RST,GPIO.IN)

PV = [
	0,1,2,3,4,5,6,7,8,9,
	10,11,12,13,14,15,16,17,18,19,
	20,21,22,23,24,25,26,27,28,29,
	30,31,32,33,34,35,36,37,38,39,
	40,42,44,46,48,50,52,54,56,58, # +2
	60,62,64,66,68,70,72,74,76,78, # +2
	80,82,84,86,88,90,92,94,96,98, # +2
	100,105,110,115,120,125,130,135,140,145, # +5
	150,155,160,165,170,175,180,185,190,195, # +5 
	200,205,210,215,220,225,230,235,240,245, # +5
	250,255,260,265,270,275,280,285,290,295, # +5
	300,305,310,315,320,325,330,335,340,345, # +5
	350,355,360,365,370,375,380,385,390,395, # +5
	400,410,420,430,440,450,460,470,480,490,
	500,510,520,530,540,550,560,570,580,590,
	600,610,620,630,640,650,660,670,680,690,
	700,720,740,760,780,800,820,840,860,880,
	900,915,930,945,960, 975, 990,1005,1030,1045,
	1060,1075,1090,1105,1120,1135,1150,1165,1180,1200,
	1220,1240,1260,1280,1300,1320,1340,1360,1380,1400,
	1420,1450,1480,1510,1540,1570,1600,1630,1660,1690,
	1720,1750,1780,1820,1850,1880,1910,1940,1970,2000,
	2050,2100,2150,2200,2250,2300,2350,2400,2450,2500,
	2550,2600,2650,2700,2750,2800,2850,2900,2950,3000,
	3050,3100,3150,3200,3250,3300,3350,3400,3450,3500,
	3600,3700,3800,3900,4000,4095
	]

# PCA9685-PWM-Board
pwm = PWM(0x40)
pwm.setPWMFreq(400)
PWM_CHANNELS=16
channels=[]
for i in range(PWM_CHANNELS):
	pwm.setPWM(i,0,0)
	channels.append(0)

led=LED_RED

def gpio_callback(gpio_id, val):
	print("gpio %s: %s" % (gpio_id, val))
	if gpio_id == 10:
		if val:
			pwm.setPWM(1, 0, 0)
		else:
			pwm.setPWM(1, 0, 4000)
	
def socket_callback(socket, val):
    print("socket %s: '%s'" % (socket.fileno(), val))
    socket.send("echo: %s\n" % val)

# GPIO interrupt callbacks
GPIO.add_interrupt_callback(9, gpio_callback)
GPIO.add_interrupt_callback(10, gpio_callback)

# TCP socket server callback on port 8080
#GPIO.add_tcp_callback(4000, socket_callback)

# Blocking main epoll loop
GPIO.wait_for_interrupts(threaded=True)

############################################################################

class ConnectionHandler(SocketServer.BaseRequestHandler):
	def version(self):
		ret = "pio sw-rev 0.1 JensLeuschner 2015\n"
		self.request.send(ret+"\n")
	
	def relay_usage(self):
		ret = "relay            : Status of all Relays\n"
		ret+= "relay x          : Status of Relay x (0 - "+str(len(RELAYS)-1)+")\n"
		ret+= "relay x [on|off] : Set Relay x (0 - "+str(len(RELAYS)-1)+")\n"
		self.request.send(ret+"\n")

	def json_data(self):
		ret = { 'version' : 'pio sw-rev 0.2 JensLeuschner 2015' }
		j=[]
		for i in range(0,len(RELAYS)):
			j.append(1);
			if GPIO.input(RELAYS[i]):
				j[i]=0
			else:
				j[i]=1
		ret['relays'] = j
		ret['pwm'] = channels
		self.request.send(json.dumps(ret)+"\n")

	def json_set(self,obj):
		if 'relays' in obj:
			for i in range(0, len(obj['relays'])):
				if obj['relays'][i]['value']:
					GPIO.output(RELAYS[int(obj['relays'][i]['id'])], GPIO.LOW)
				else:
					GPIO.output(RELAYS[int(obj['relays'][i]['id'])], GPIO.HIGH)
		if 'pwm' in obj:
			for i in range(0, len(obj['pwm'])):
				pwm.setPWM(int(obj['pwm'][i]['id']),0,PV[int(obj['pwm'][i]['value'])])
				channels[int(obj['pwm'][i]['id'])] = int(obj['pwm'][i]['value'])
		self.json_data()
	
	def relay_status(self,id):
		if GPIO.input(RELAYS[id]):
			ret="Relay " + str(id) + " Status: OFF"
		else:
			ret = "Relay " + str(id) + " Status: ON"
		self.request.send(ret+"\n")

	def pwm_usage(self):
		ret = "pwm            : Status of all PWM-Channels\n"
		ret+= "pwm x          : Status of PWM-Channel x (0 - "+str(PWM_CHANNELS-1)+")\n"
		ret+= "pwm x [0-255]  : Set PWM-Channel x (0 - "+str(PWM_CHANNELS-1)+")\n"
		ret+= "pwm set [list] : Set PWM-Channels by Comma-separated List\n"
		self.request.send(ret+"\n")

	def pwm_status(self,id):
		ret = "PWM "+str(id)+ " : " +str(channels[id])
		self.request.send(ret+"\n")
		
	def handle(self):
		print self.client_address
		talk=True
		reply=''
		while (talk):
			self.request.send(PROMPT)
			data = self.request.recv(1024).strip()
			words = data.split(' ')
			if words[0] == 'exit':
				talk=False
				break
			if words[0] == 'version':
				self.version()
				continue
			if words[0] == 'json':
				if len(words) > 1:
					self.json_set(json.loads(' '.join(words[1:])))
				else:
					self.json_data()
				continue
			if words[0] == 'relay':
				if len(words) > 1:
					if words[1].isdigit() and int(words[1]) >= 0 and int(words[1]) < len(RELAYS):
						if len(words) > 2:
							if words[2] == "1" or words[2] == "on":
								GPIO.output(RELAYS[int(words[1])], GPIO.LOW)
							else:
								GPIO.output(RELAYS[int(words[1])], GPIO.HIGH)
							self.relay_status(int(words[1]))
						else:
							self.relay_status(int(words[1]))
					else:
						self.relay_usage()
				else:
					for i in range(0,len(RELAYS)):
						self.relay_status(i)
				continue
			if words[0] == 'pwm':
				if len(words) > 1:
					if words[1].isdigit() and int(words[1]) >= 0 and int(words[1]) < PWM_CHANNELS:
						if len(words) > 2:
							if words[2].isdigit() and int(words[2]) >0 and int(words[2]) < 256:
								pwm.setPWM(int(words[1]),0,PV[int(words[2])])
								channels[int(words[1])] = int(words[2])
							else:
								pwm.setPWM(int(words[1]),0,0)
								channels[int(words[1])] = 0
							self.pwm_status(int(words[1]))
						else:
							self.pwm_status(int(words[1]))
					else:
						if words[1] == "set":
							if len(words) > 2:
								chs = words[2].split(',')
								c=0
								for ch in chs:
									if ch.isdigit() and int(ch) >= 0 and int(ch) < 256:
										pwm.setPWM(c,0,PV[int(ch)])
										channels[c] = int(ch)
									c+=1
								for i in range(0,PWM_CHANNELS):
									self.pwm_status(i)
							else:
								self.pwm_usage()
						else:
							self.pwm_usage()
				else:
					for i in range(0,PWM_CHANNELS):
						self.pwm_status(i)
				continue
			self.version()
			ret = "Usage:  ('cmd help' for further help)\n"
			ret+= "version Show pio Version\n"
			ret+= "relay   Relay commands\n"
			ret+= "pwm     PWM-Channel commands\n"
			ret+= "json    get/set complete IO-Status in JSON-Format\n"
			ret+= "exit    Close Connection\n"
			ret+= "help    This Text\n"
			self.request.send(ret+"\n")
			
			try:
				words = data.split(',')
				#reply=words.pop(0)
				i=0
				for pair in words:
					if i>=CHANNELS:
						break
					if pair=="":
						i+=1
						continue
					part=pair.split('.')
					#fadeTo[i][0]=int(part[0])
					#if len(part)>1:
					#    fadeTo[i][1]=int(part[1])
					#else:
					#    fadeTo[i][1]=0
					i+=1
			except:
				pass
			#talk=False
			#if reply is not None:
			#	self.request.send(reply)
		#reply=str(channel)+'\n'
		#reply='Gotit\n'
		#self.request.send(reply)
		self.request.close()

############################################################################
class Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(\
        self,\
        server_address,\
        RequestHandlerClass)
        print "Started Server: ", server_address
############################################################################




if __name__ == "__main__":
	GPIO.output(led, GPIO.HIGH)
	server = Server((HOST, PORT), ConnectionHandler)
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print "Keyboard interrupt, shutting down"
		run=False
		server.shutdown()
		fader.join()

	i=0
	while 1:
		for i in range(0,255):
			#print i," : ",PV[i]
			#pwm.setPWM(0,0,PV[i])
			#pwm.setPWM(1,0,PV[i])
			pwm.setPWM(2,0,PV[i])
			#time.sleep(0.001)
		for i in range(254,1,-1):
			#print i," : ",PV[i]
			#pwm.setPWM(0,0,PV[i])
			#pwm.setPWM(1,0,PV[i])
			pwm.setPWM(2,0,PV[i])
			#time.sleep(0.001)
