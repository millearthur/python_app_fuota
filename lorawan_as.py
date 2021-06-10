from chirpstack_api.as_pb import integration

import json

import grpc
from chirpstack_api.as_pb.external import api

#DO DEBUG PRINT ?
debug = 0


# Configuration.
# Point to the API interface of the main server
as_server = "localhost:8080"

# The API token (retrieved using the web-interface).
as_api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcGlfa2V5X2lkIjoiYzgyMTc5N2UtOTkyYi00ZDc0LTg0N2EtNzE5YmM0MzRmMjgzIiwiYXVkIjoiYXMiLCJpc3MiOiJhcyIsIm5iZiI6MTYyMDM4ODEyMywic3ViIjoiYXBpX2tleSJ9.cb1uBPG-I4xD7vkqY0o5lgXv1HAFpEmk8sX1VlHXhZ8"

# Connect without using TLS.
channel_as = grpc.insecure_channel(as_server)

# Device-queue API client.
as_Queue = api.DeviceQueueServiceStub(channel_as)


class lorawan_as():
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
        
    