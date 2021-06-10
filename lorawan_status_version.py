from lorawan_as import *
from device_list import *

class lorawan_status_version() :

    def __init__(self,lorawan_as,device_list):
        self.lorawan_as = lorawan_as
        self.device_list = device_list
        
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
            
        if debug == 1:
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
                self.device_list.update_device_list(dev_eui,{
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
            self.device_list.update_device_list(dev_eui,{
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
                self.device_list.update_device_list(dev_eui,{
                    slot : slotVersion,
                })

    def handleSpaceStatusAns(self,dev_eui,payload):
        if (len(payload) < 8):
            print("lenght of received is too short")
        else:
            heap = int.from_bytes(payload[0:4],"little")
            slotSize = int.from_bytes(payload[4:8],"little")
            self.device_list.update_device_list(dev_eui,{
                "heap_available"      : heap,
                "slot_size"      : slotSize,
            })

    def handleUpTimeAns(self,dev_eui,payload):
        if (len(payload) < 4):
            print("lenght of received is too short")
        else:
            uptime = int.from_bytes(payload[0:4],"little")
            self.device_list.update_device_list(dev_eui,{
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
                self.device_list.update_device_list(dev_eui,{
                    "manufacturer_id"      : string,
                })
            if ((payload[0] & 0b01) == 0b01) : 
                #Device id is present
                length = payload[nbString]
                nbString += 1
                string = str(payload[nbString:nbString+length],'UTF-8')
                nbString += length #current offset + length
                self.device_list.update_device_list(dev_eui,{
                    "device_id"      : string,
                })

    #Definitions to send packets to device
    def askPackageVersion(self,dev_eui):
        print("Requests Package version of" + dev_eui)
        toSend = bytes([0x00])
        self.lorawan_as.send(dev_eui,111,toSend)

    def askVersionRunning(self,dev_eui):
        print("Requests running version of " + dev_eui)
        toSend = bytes([0x01])
        self.lorawan_as.send(dev_eui,111,toSend)


    def askVersionStored(self,dev_eui):
        print("Requests stored version of " + dev_eui)
        nbSlot = 3
        storedInfoParam = ((0x0F & 0) | (0xF0 & nbSlot))
        toSend = bytes([0x02 , storedInfoParam])
        self.lorawan_as.send(dev_eui,111,toSend)

    def askSpaceStatus(self,dev_eui):
        print("Requests space status of " + dev_eui)
        toSend = bytes([0x03])
        self.lorawan_as.send(dev_eui,111,toSend)

    def askUpTime(self,dev_eui):
        print("Requests uptime of " + dev_eui)
        toSend = bytes([0x04])
        self.lorawan_as.send(dev_eui,111,toSend)

    def askEraseSlot(self,dev_eui,slot):
        print("Requests Erase slot0 of " + dev_eui)
        if slot == '0' : 
            toSend = bytes([0x05, 0x00])
            self.lorawan_as.send(dev_eui,111,toSend)
        elif slot == '1':
            toSend = bytes([0x05, 0x01])
            self.lorawan_as.send(dev_eui,111,toSend)
        else:
            if debug : print("slot to erase is not specified, so do nothing")

    def askDeviceID(self,dev_eui):
        print("Requests Device ID of " + dev_eui)
        toSend = bytes([0x06, 0x03])
        self.lorawan_as.send(dev_eui,111,toSend)