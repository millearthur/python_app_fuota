import grpc
from chirpstack_api import fuota

from google.protobuf import duration_pb2
from Crypto.Cipher import AES


#DO DEBUG PRINT ?
debug = 0


# Configuration.
# Point to the API interface of the fuota server
fuota_server = "localhost:8070"

# Connect without using TLS.
channel_fuota = grpc.insecure_channel(fuota_server)

# Device-queue API client.
client_fuota = fuota.FUOTAServerServiceStub(channel_fuota)


class lorawan_deployment() :
  def __init__(self):
      self.deploymentData = {}


  def update_deployment(self,dev_eui_list, binaryPath, key):
    self.deploymentData.update({
      'dev_eui_list' : dev_eui_list,
      'binary' : binaryPath,
      'genAppKey' : key
    })
    print("stored basic deployment data")
    print(self.deploymentData)
    
  def update_deployment(self,dev_eui_list, binaryPath, key, datarate, f_size, frequency, timeout, redundancy):
    #verify f_size depending on dr
    #The maximum payload considers the overhead included by the fragmentation process
    # NB: - from specification : 2bytes
    #     - from testing : 3 bytes (execpte DR4/5 where ok)
    if (datarate == 5):
      f_size = min(222,f_size)
    elif (datarate == 4):
      f_size = min(222,f_size)
    elif (datarate == 3):
      f_size = min(112,f_size)
    elif (datarate == 2):
      f_size = min(48,f_size)
    elif (datarate == 1):
      f_size = min(48,f_size)
    elif (datarate == 0):
      f_size = min(17,f_size) #even lower due to the time on air betweem transmissions
    else :
      datarate = 5
      f_size = 222
    
    self.deploymentData.update({
      'dev_eui_list' : dev_eui_list,
      'binary' : binaryPath,
      'genAppKey' : key,
      'datarate' : datarate,
      'f_size' : f_size,
      'frequency' : frequency,
      'timeout' : timeout,
      'redundancy' : redundancy
    })
    print("stored advanced deployment data")
    print(self.deploymentData)

  def GetMcRootKeyFromGenAppKey(self,key):
    #takes key argument as hex string, and returns a bytes array
    cipher = AES.new(bytes.fromhex(key), AES.MODE_ECB)
    ciphertext = cipher.encrypt(bytes(16))
    return ciphertext

  def start_deployment(self):
    print("to use deployment data : ")
    print(self.deploymentData)
    # opens a file
    file_data = open(self.deploymentData['binary'],'rb')
    data = file_data.read()
    # end of file

    # Creates a device and a deployment
    main_deploy = fuota.Deployment()
    main_deploy.application_id = 1

    #add all devices
    for dev_eui in self.deploymentData['dev_eui_list'] :
      device_a = fuota.DeploymentDevice()
      device_a.dev_eui = bytes.fromhex(dev_eui)
      device_a.mc_root_key = self.GetMcRootKeyFromGenAppKey(key = self.deploymentData['genAppKey'])
      if debug == 1 : 
        print("-> device to add to deployment ", end="")
        print(device_a)

      main_deploy.devices.extend([device_a])

    #defaults to classC
    main_deploy.multicast_group_type  = fuota.MulticastGroupType.CLASS_C
    #use custom DR
    try : 
      main_deploy.multicast_dr = self.deploymentData['datarate']
    except:
      main_deploy.multicast_dr = 5
    
    #use custom Freq
    try : 
      main_deploy.multicast_frequency = self.deploymentData['frequency']
    except:
      main_deploy.multicast_frequency = 868100000
    
    main_deploy.multicast_group_id = 0
    main_deploy.multicast_timeout = 40
    
    #use custom timeout
    try : 
      main_deploy.unicast_timeout.FromSeconds(self.deploymentData['timeout'])
    except:
      main_deploy.unicast_timeout.FromSeconds(150)
      
    main_deploy.unicast_attempt_count = 5
    
    #use custom data
    main_deploy.payload = data
    
    #use custom fragment_size
    try : 
      main_deploy.fragmentation_fragment_size = self.deploymentData['f_size']
    except:
      main_deploy.fragmentation_fragment_size = 220
    
    #use custom redundancy
    try : 
      main_deploy.fragmentation_redundancy = self.deploymentData['redundancy']
    except:
      main_deploy.fragmentation_redundancy = 10
      
    main_deploy.fragmentation_session_index = 0
    main_deploy.fragmentation_matrix = 0
    main_deploy.fragmentation_block_ack_delay = 1
    main_deploy.fragmentation_descriptor = bytes([0, 0, 0, 0])
    main_deploy.request_fragmentation_session_status = fuota.RequestFragmentationSessionStatus.NO_REQUEST

    print("deployment prepared with values :")
    print(main_deploy)

    client_fuota.CreateDeployment(
      fuota.CreateDeploymentRequest(deployment = main_deploy)
      )
    print("deployment sent")
    # end of deployment