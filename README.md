# Python APP - FUOTA Chirpstack

This repo represents a python application that can be used to get a list of informations from a LoRaWan application.

The first part of the interface is a simple interface showing the devices connected to the server. You can display informations about the device, including the data retrived in the last transmission from the device.

The second part is the fuota interface. It allows you to select informations about a specific deployement. Once the various values are setup, the deployement can be sent to the fuota server to execute the actual data transmission over LoraWan.

This whole application runs by starting the application_server : 

```
$ python3 application_server.py
```

## HTTP Serveur

This application runs a basic `BaseHTTPRequestHandler` http python server. It is used to retrieved informations posted by the application serveur, but also to communicate with the user browser.

The server currently listens on port 8091, and the broswer can retreive the main page with either : `/main.html` or `/`

The `Handler` is able to handle GET request, to provide for the main page, and answer the data request update from the client page. I can also hanlde POST request, for the orders given by the client page, like sending a specific transmission to the end device.

The server also handles a basic authentication when a new client connects to the server, in order to retreive the page.

In the main handleGET/POST function, the operation desired by the client is identified by parsing the request. The correct function is then called, with the right arguments.

## Using Chirpstack-Application-Server

The server is able to handle the data and current status of an application server. The server `Chirpstack-Application-Server` is then configured to have his REST integration sending data to the python server. In our case using localhost:8091.
As said earlier, the server will then parse the request and handle the data sent. In this case the server only listens for transmissions.

The python server can also send data to a specific device. In order to do that, it will use the `lorawan_as.py` file. In this class, the adress and port of the application server is specified, as well as the API token to allow the program to authenticate on the server.

The connection to the server is opened, and the class provides a `send` interface, in order to allow the main program to sent data on a speficied port, to a specified device (indentified by its DevEUI).

The function requests the application server to place this message in the queue of downlink messages to the device.

## Using Chirpstack-Fuota-Server

The communication to the fuota server is done in the `lorawan_deployement.py` file.

The program uses the `chirpstack-api` to know how to interface with the fuota server.
This can be installed with the Python Packet Manager : 

```
$ pip3 install chirpstack-api
```

The server will then connect to the `chirpstack-fuota-server` running : in our case the adress used is : `localhost:8070`.

NOTE that the version of the chirpstack API and the FuotaServer must match to have the correct interface to the server. The current release can support fuota-server v3.0.0; and the chirpstack-api v3.10.

The FUOTA part of the web interface allow to configure the data to send to the device, as well as multiple informations about the deployement, including the multicast and fragmentation setup options, etc...

By default the program will be able to scan the `bin/` to add new binaries to the application. With this basic feature, the program won't be able to know the fuota information of the file (patch or not, which algo etc..). This feature could be added in the future, if the informations are correctly formatted in the binary. Currently, this informations can be displayed in the Web Interface if the user manually sets them is the main program, under the `binaries_list`


## Specification

The python server includes the implementation of the server-side specification for lorawan : `LoRaWAN Version and Status Specification_v0_2` see [Specifiation](./LoRaWAN Version and Status Specification_v0_2.pdf)

This implementation is done in the `lorawan_status_version.py` file. The file provides a handle function that can be called with the payload received on port 110, to be handled. The file also provide the interface to send the request to the device.
The values that are sent to the device have been pre setup in the file, but this can be changed if the specification is updated or if the deployement envorinmemt if modified.


