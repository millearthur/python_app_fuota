from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from chirpstack_api.as_pb import integration
from google.protobuf.json_format import Parse

import os
import sys
import time
from datetime import datetime

import base64

import json

import grpc
from chirpstack_api.as_pb.external import api
from chirpstack_api import fuota

from google.protobuf import duration_pb2

from Crypto.Cipher import AES

from lorawan_deployement import *

#DO DEBUG PRINT ?
debug = 0


# Configuration.
# Point to the API interface of the main server
as_server = "localhost:8080"
# Point to the API interface of the fuota server
fuota_server = "localhost:8070"

# The API token (retrieved using the web-interface).
as_api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5X2lkIjoiYzgyMTc5N2UtOTkyYi00ZDc0LTg0N2EtNzE5YmM0MzRmMjgzIiwiYXVkIjoiYXMiLCJpc3MiOiJhcyIsIm5iZiI6MTYyMDM4ODEyMywic3ViIjoiYXBpX2tleSJ9.cb1uBPG-I4xD7vkqY0o5lgXv1HAFpEmk8sX1VlHXhZ8"

key = base64.b64encode(
            bytes('%s:%s' % ('admin', 'chirpstack'), 'utf-8')).decode('ascii')

print("start\n",end="")
print("Hello World")


# Connect without using TLS.
channel_as = grpc.insecure_channel(as_server)
channel_fuota = grpc.insecure_channel(fuota_server)

# Device-queue API client.
as_Queue = api.DeviceQueueServiceStub(channel_as)
client_fuota = fuota.FUOTAServerServiceStub(channel_fuota)



# McRoot key generated using go program TODO: IMPLEMENT MCROOT GENERATION
#mcRootKeyA, err := multicastsetup.GetMcRootKeyForGenAppKey(lorawan.AES128Key{ 0x35, 0x0b, 0x7f, 0x62, 0xcf, 0x56, 0xab, 0x3e, 0xfe, 0x9e, 0x2c, 0xc7, 0x24, 0xe8, 0x3f, 0x43})  //Node C chirpstack genapp = appkey

# raw value "90e44345329dd05ce834e3d3cbcf3025"
mcRootKeyA =  bytes([0x90, 0xe4, 0x43, 0x45, 0x32, 0x9d, 0xd0, 0x5c, 0xe8, 0x34, 0xe3, 0xd3, 0xcb, 0xcf, 0x30, 0x25])

# in device list, devices should be identified by a hexstring corresponding to their devEUI
# inside a device, there can be various fields, they can be filled as events happens

device_list = {
  '0080000004006aa0' : {
      "device_name"   : 'NodeTest',
      "application_name" : 'LoraAppTest',}
}

try : 
  binaries_list = { 
    'bin/patch_demo_ddelta_v1v2.bin_signed' : {
      'size' : os.path.getsize("bin/patch_demo_ddelta_v1v2.bin_signed"),
      'is_update' : True,
      'target'    : 'DISCO',
      'update_type' : 'DDELTA',
      'update_z' : 'Arithmetic', 
    },
    'bin/patch_demo_jdiff_v1v2.bin_signed' : {
      'size' : os.path.getsize("bin/patch_demo_jdiff_v1v2.bin_signed"),
      'is_update' : True,
      'target'    : 'DISCO',
      'update_type' : 'JDIFF',
    },
    'bin/patch_ddelta_v100_v200.bin_signed' : {
      'size' : os.path.getsize('bin/patch_ddelta_v100_v200.bin_signed'),
      'is_update' : True,
      'target' : 'DISCO',
      'update_type': 'DDELTA',
    } ,
    'bin/patch_jdiff_v100_v200.bin_signed' : {
      'size' : os.path.getsize('bin/patch_jdiff_v100_v200.bin_signed'),
      'is_update' : True,
      'target' : 'DISCO',
      'update_type': 'JPATCH',
    },
    'bin/patch_ddelta_v101_v201.bin_signed' : {
      'size' : os.path.getsize('bin/patch_ddelta_v101_v201.bin_signed'),
      'is_update' : True,
      'target' : 'DISCO',
      'update_type': 'DDELTA',
    } ,
    'bin/patch_jdiff_v101_v201.bin_signed' : {
      'size' : os.path.getsize('bin/patch_jdiff_v101_v201.bin_signed'),
      'is_update' : True,
      'target' : 'DISCO',
      'update_type': 'JPATCH',
    }
  }
except: 
  binaries_list = {
}

#dev_eui should be in stored state ie: str of hex
#data should be a dic of attribute/value of device
def update_device_list(dev_eui,data):
  global device_list
  
  if debug == 1 : 
    print("-> Before : ", end="")
    print(device_list)
  if dev_eui in device_list : 
    device_list[dev_eui].update(data)
  else :
    device_list.update({
      dev_eui : data
    })
  if debug == 1 : 
    print("-> After : ", end="")
    print(device_list)



class LoraWanStatusVersion() :
  global device_list

  #HandleReceptions (Stores infos to devices_list)
  def handleRcvMsg(self,dev_eui,payload):
    print("Status/Version message received ... ")
    print("Payload is " + str(payload))
    if (len(payload) < 1):
      print("lenght of received is too short : don't carry command")
    else : 
      if(payload[0] == 0x00):
        #packageVersionAns
        self.handlePackageVersionAns(dev_eui = dev_eui, payload = payload[1:])
      elif (payload[0] == 0x01):
        #versionRunningAns
        self.handleVersionRunningAns(dev_eui = dev_eui, payload = payload[1:])
      elif (payload[0] == 0x02):
        #versionStoredAns
        self.handleVersionStoredAns(dev_eui = dev_eui, payload = payload[1:])
      elif (payload[0] == 0x03):
        #spaceStatusAns
        self.handleSpaceStatusAns(dev_eui = dev_eui, payload = payload[1:])
      elif (payload[0] == 0x04):
        #upTimeAns
        self.handleUpTimeAns(dev_eui = dev_eui, payload = payload[1:])
      elif (payload[0] == 0x06):
        #ID
        self.handleDeviceIDAns(dev_eui = dev_eui, payload = payload[1:])
      else : 
        print("Command not implemented")
    if debug == 1 : 
      print("-> End of handling : ", end="")
      print(device_list)
      

  def handlePackageVersionAns(self,dev_eui,payload):
    if (len(payload) < 3):
      print("lenght of received is too short")
    else:
      packageId =       payload[0]
      packageVersion =  payload[1]
      versionInfo =     payload[2]
      versionType =   (versionInfo & 0xf0)>>4
      nbSlot =        (versionInfo & 0x0f)
      versionStrType = ""
      if (versionType <= 0 | versionType > 2): 
        versionStrType = "Not supported"
      elif (versionType == 1): 
        versionStrType = "Major:Minor:Patch"
      elif (versionType == 2): 
        versionStrType = "Sec Timestamp"
      print("On device implementation is :")
      print("packageId      :" + str(packageId))
      print("packageVersion :" + str(packageVersion))
      print("Versioning Type:" + str(versionStrType))
      update_device_list(dev_eui,{
          "package_version" : packageVersion,
          "versioning_type" : versionStrType
          })


  def handleVersionRunningAns(self,dev_eui,payload):
    if (len(payload) < 5):
      print("lenght of received is too short")
    else:
      runningSlot =(0x0F & payload[0])
      print("considering slot" + str(runningSlot))
      slotVersion = int.from_bytes(payload[1:5],"little")
      slot = "version_slot"+ str(runningSlot)
      print("version is :" + str(slotVersion))
      update_device_list(dev_eui,{
          slot : slotVersion,
      })

  def handleVersionStoredAns(self,dev_eui,payload):
    if (len(payload) < 5):
      print("lenght of received is too short")
    else:
      nbSlot = (0x0F & payload[0])
      for i in range(0 , (nbSlot-1)):
        print("considering slot" + str(i))
        slotVersion = int.from_bytes(payload[(1+i*4):(5+i*4)],"little")
        slot = "version_slot"+ str(i)
        print("version is :" + str(slotVersion))
        update_device_list(dev_eui,{
          slot : slotVersion,
        })

  def handleSpaceStatusAns(self,dev_eui,payload):
    if (len(payload) < 8):
      print("lenght of received is too short")
    else:
      heap = int.from_bytes(payload[0:4],"little")
      slotSize = int.from_bytes(payload[4:8],"little")
      update_device_list(dev_eui,{
          "heap_available"      : heap,
          "slot_size"      : slotSize,
      })

  def handleUpTimeAns(self,dev_eui,payload):
    if (len(payload) < 4):
      print("lenght of received is too short")
    else:
      uptime = int.from_bytes(payload[0:4],"little")
      update_device_list(dev_eui,{
          "up_time"      : uptime,
      })

  def handleDeviceIDAns(self,dev_eui,payload):
    if (len(payload) < 1):
      print("lenght of received is too short")
    else:
      print("payload to analyse is :" , end="")
      print(payload)
      #payload[0] is the flags answer 
      nbString = 1

      if ((payload[0] & 0b10) == 0b10) :
        #Manufacturer id is present
        length = payload[nbString]
        nbString += 1
        string = str(payload[nbString:nbString+length],'UTF-8')
        nbString += length #current offset + length
        update_device_list(dev_eui,{
          "manufacturer_id"      : string,
        })
        
      if ((payload[0] & 0b01) == 0b01) : 
        #Device id is present
        length = payload[nbString]
        nbString += 1
        string = str(payload[nbString:nbString+length],'UTF-8')
        nbString += length #current offset + length
        update_device_list(dev_eui,{
          "device_id"      : string,
        })

  #Definitions to send packets to device
  def askPackageVersion(self,dev_eui):
    print("Requests Package version of" + dev_eui)
    toSend = bytes([0x00])
    self.send(dev_eui,111,toSend)

  def askVersionRunning(self,dev_eui):
    print("Requests running version of " + dev_eui)
    toSend = bytes([0x01])
    self.send(dev_eui,111,toSend)


  def askVersionStored(self,dev_eui):
    print("Requests stored version of " + dev_eui)
    nbSlot = 3
    storedInfoParam = ((0x0F & 0) | (0xF0 & nbSlot))
    toSend = bytes([0x02 , storedInfoParam])
    self.send(dev_eui,111,toSend)

  def askSpaceStatus(self,dev_eui):
    print("Requests space status of " + dev_eui)
    toSend = bytes([0x03])
    self.send(dev_eui,111,toSend)

  def askUpTime(self,dev_eui):
    print("Requests uptime of " + dev_eui)
    toSend = bytes([0x04])
    self.send(dev_eui,111,toSend)

  def askEraseSlot(self,dev_eui,slot):
    print("Requests Erase slot0 of " + dev_eui)
    if slot == '0' : 
      toSend = bytes([0x05, 0x00])
      self.send(dev_eui,111,toSend)
    elif slot == '1':
      toSend = bytes([0x05, 0x01])
      self.send(dev_eui,111,toSend)
    else:
      if debug : print("slot to erase is not specified, so do nothing")
    
  def askDeviceID(self,dev_eui):
    print("Requests Device ID of " + dev_eui)
    toSend = bytes([0x06, 0x03])
    self.send(dev_eui,111,toSend)


  #Sending Data
  def send(self,dev_eui,port,payload):
    # Define the API key meta-data.
    auth_token = [("authorization", "Bearer %s" % as_api_token)]

    # Construct request.
    req = api.EnqueueDeviceQueueItemRequest()
    req.device_queue_item.confirmed = False
    req.device_queue_item.data = bytes(payload) #TODO: verify payload type
    req.device_queue_item.dev_eui = dev_eui     #TODO: verify dev_eui type
    req.device_queue_item.f_port = port

    resp = as_Queue.Enqueue(req, metadata=auth_token)
    
    print("Sending on port " + str(port) + " ; reported count : " + str(resp.f_cnt))



class Handler(BaseHTTPRequestHandler):
  global LWDeployment
  # True -  JSON marshaler
  # False - Protobuf marshaler (binary)
  isJson = False

  def handlePost(self):
    ### HANDLING POST RQST ###
    self.send_response(200)
    self.end_headers()

    query_args = parse_qs(urlparse(self.path).query)  #Parse args from reception
    content_len = int(self.headers.get('Content-Length', 0)) #Get lenght of args
    body = self.rfile.read(content_len)               #Get content

    if "/lorawan/send" in self.path :
      eui = query_args['eui'][0]
      cmd = query_args['cmd'][0]
      if cmd == '00' : 
        StatusVersion.askPackageVersion(eui)
      elif cmd == '01' :
        StatusVersion.askVersionRunning(eui)
      elif cmd == '02' :
        StatusVersion.askVersionStored(eui)
      elif cmd == '03' :
        StatusVersion.askSpaceStatus(eui)
      elif cmd == '04' :
        StatusVersion.askUpTime(eui)
      elif cmd == '05' :
        slot = query_args['slot'][0]
        StatusVersion.askEraseSlot(eui,slot=slot)
      elif cmd == '06' :
        StatusVersion.askDeviceID(eui)
      else : 
        print("Command not found")
    elif "/lorawan/deployment/set" in self.path :
      eui = query_args['eui']
      binary = query_args['bin'][0]
      genAppkey = query_args['key'][0]
      LWDeployment.update_deployment(dev_eui_list = eui, binaryPath = binary, key=genAppkey)
    elif "/lorawan/deployment/start" in self.path :
      LWDeployment.start_deployment()
    else: 
      if (len(query_args) > 0):
        #data received from chirpstack
        self.lorawan_event(body,query_args)
      else : 
        #data received from chirpstack
        print("other data rcved")
    ### ---------- ###


  def handleGet(self):
    ### HANDLING GET RQST ###
    print("rcved get : " + self.path)
    #Redirect root
    if self.path == '/':
        self.path = '/main.html'
    #deliver page

    if "/lorawan/" in self.path : 
      #lorawan app request
      if self.path == "/lorawan/device_list/":
        self.send_Device_List()
      elif "/lorawan/device_details" in self.path:
        eui = parse_qs(urlparse(self.path).query)['eui'][0]
        print("requested eui " + str(eui))
        #print("requested eui " + (eui))
        self.send_Device_details(str(eui))
      elif self.path == "/lorawan/update_list/":
        self.send_Update_List()
      elif self.path == "/lorawan/deployment_list/":
        self.send_Deployment_List()
      else : 
        print("Cannot handle request")
    else:
      try:
          print("open : " + self.path)
          file = open(self.path[1:],'rb').read()
          self.send_response(200)
      except:
          file = bytes("404; File not found" , 'utf-8')
          self.send_response(404)
      self.end_headers()
      self.wfile.write(file)
      ### ---------- ###


  def do_AUTHHEAD(self):
      self.send_response(401)
      self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
      self.send_header('Content-type', 'text/html')
      self.end_headers()


  # ----------- HANDLE WEB EVENT -------------
  def do_GET(self):
    global key

    if self.headers.get('Authorization') == None:
        self.do_AUTHHEAD()
        self.wfile.write(bytes('no auth header received', 'utf-8'))
        return
    elif self.headers.get('Authorization') == 'Basic ' + str(key):
      self.handleGet()
    else:
        self.do_AUTHHEAD()
        self.wfile.write(bytes(self.headers.get('Authorization'), 'utf-8'))
        self.wfile.write(bytes('not authenticated', 'utf-8'))
        return

    

  def do_POST(self):
    global key

    #print(self.client_address)
    #print(self.client_address[0])

    if(self.client_address[0] == '127.0.0.1'):
      #request from localhost
      self.handlePost()

    else: 
      ## Message from outside localhost
      if self.headers.get('Authorization') == None:
          self.do_AUTHHEAD()
          self.wfile.write(bytes('no auth header received', 'utf-8'))
          return
      elif self.headers.get('Authorization') == 'Basic ' + str(key):
        self.handlePost()

      else:
          self.do_AUTHHEAD()
          self.wfile.write(bytes(self.headers.get('Authorization'), 'utf-8'))
          self.wfile.write(bytes('not authenticated', 'utf-8'))
          return

  # ----------- HANDLE APP REQUEST -------------
  def send_Device_List(self) :
    global device_list

    answer = bytes([])
    device_short_list = {}
    for eui in device_list:
      print("eui is :" + str(eui))
      device_short_list.update({eui : {
          "device_name"      : device_list[eui]['device_name'],
          "application_name" : device_list[eui]['application_name'],
      }, })
    if debug == 1 : 
      print("-> Devices short list : ", end="")
      print(device_short_list)
    self.send_response(200)
    answer = json.dumps(device_short_list).encode()

    self.end_headers()
    self.wfile.write(answer)

  def send_Device_details(self,dev_eui) :
    global device_list

    self.send_response(200)
    self.end_headers()
    self.wfile.write(json.dumps(device_list[dev_eui]).encode())
  
  def send_Update_List(self) :
    self.send_response(200)
    self.end_headers()
    self.wfile.write(json.dumps(binaries_list).encode())

  def send_Deployment_List(self) :
    try:
      self.send_response(200)
      self.end_headers()
      self.wfile.write(json.dumps(LWDeployment.deploymentData).encode())
    except:
      self.send_response(404)
      self.end_headers()
      self.wfile.write(bytes("404; File not found" , 'utf-8'))

  # ----------- HANDLE LORA EVENT -------------
  def lorawan_event(self, body, query_args):
    if query_args["event"][0] == "up":
        self.up_event(body)
    elif query_args["event"][0] == "join":
        self.join_event(body)
    else:
        print("handler for event %s is not implemented" % query_args["event"][0])

  def up_event(self, body):
    global device_list 
    
    up = self.unmarshal(body, integration.UplinkEvent())
    print("Uplink received from: %s with payload: %s" % (up.dev_eui.hex(), up.data.hex()))
    
    if (up.f_port == 111):
      StatusVersion.handleRcvMsg(up.dev_eui.hex(),up.data)

    update_device_list(up.dev_eui.hex(),{
        "dev_addr"      : up.dev_addr.hex(),
        "device_name"   : up.device_name,
        "application_name" : up.application_name,
        "last_up" : str(datetime.now()),
        "last_data_port" : up.f_port,
        "last_data" : up.data.hex(),
        "last_data_str" : bytearray.fromhex(up.data.hex()).decode(),
    })


  def join_event(self, body):
    global device_list
    join = self.unmarshal(body, integration.JoinEvent())
    print("Device: %s joined with DevAddr: %s" % (join.dev_eui.hex(), join.dev_addr.hex()))
    
    update_device_list(join.dev_eui.hex(),{
        "dev_addr"      : join.dev_addr.hex(),
        "device_name"   : join.device_name,
        "application_name" : join.application_name,
    })


  def unmarshal(self, body, pl):
    if self.isJson:
        return Parse(body, pl)

    pl.ParseFromString(body)
    return pl
  


httpd = HTTPServer(('', 8091), Handler)
StatusVersion = LoraWanStatusVersion()
LWDeployment = lorawan_deployement()
#StatusVersion.send(dev_eui = (bytes([0x00, 0x80, 0x00, 0x00, 0x04, 0x00, 0x6a, 0xaa]).hex()),port = 111,payload = bytes([1, 2, 3]))
httpd.serve_forever()

#start_deployment()
