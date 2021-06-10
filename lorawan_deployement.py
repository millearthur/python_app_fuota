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


class lorawan_deployement() :
  def __init__(self):
      self.deploymentData = {}
  

  def update_deployment(self,dev_eui_list, binaryPath, key):
    self.deploymentData.update({
      'dev_eui_list' : dev_eui_list,
      'binary' : binaryPath,
      'genAppKey' : key
    })
    print("stored deployment data")
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
    #file_data = open("bin/patch_signed.bin",'rb')
    file_data = open(self.deploymentData['binary'],'rb')
    data = file_data.read()
    # end of file

    # Creates a device and a deployement
    main_deploy = fuota.Deployment()
    main_deploy.application_id = 1

    for dev_eui in self.deploymentData['dev_eui_list'] :
      device_a = fuota.DeploymentDevice()
      device_a.dev_eui = bytes.fromhex(dev_eui)
      device_a.mc_root_key = self.GetMcRootKeyFromGenAppKey(key = self.deploymentData['genAppKey'])
      if debug == 1 : 
        print("-> device to add to deployement ", end="")
        print(device_a)

      main_deploy.devices.extend([device_a])

    main_deploy.multicast_group_type  = fuota.MulticastGroupType.CLASS_C
    main_deploy.multicast_dr = 5
    main_deploy.multicast_frequency = 868100000
    main_deploy.multicast_group_id = 0
    main_deploy.multicast_timeout = 40
    main_deploy.unicast_timeout.FromSeconds(150) # FromString('25') #FromSeconds(25)
    main_deploy.unicast_attempt_count = 5
    main_deploy.payload = data
    main_deploy.fragmentation_fragment_size = 200
    main_deploy.fragmentation_redundancy = 10
    main_deploy.fragmentation_session_index = 0
    main_deploy.fragmentation_matrix = 0
    main_deploy.fragmentation_block_ack_delay = 1
    main_deploy.fragmentation_descriptor = bytes([0, 0, 0, 0])

    print("deployement prepared")

    client_fuota.CreateDeployment(
      fuota.CreateDeploymentRequest(deployment = main_deploy)
      )
    print("deployement sent")
    # end of deployement