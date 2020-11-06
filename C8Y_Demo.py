import requests 				# for HTTP https://pypi.org/project/requests/
import json						# for json parsing and formatting
from datetime import datetime	# for date & time formatting in HTTP POSTs
import time						# for time.sleep() functionality
import re 						# for refular expression matching
from threading import Thread
import os
import fnmatch
from C8Y_Device import C8Y_Device
import random

tenantURL = "https://richardnagle.us.cumulocity.com/"
tenantId = "richardnagle"
deviceName = "C8Y_REST_Demo" #Name of device in Device Management
deviceType = "c8y_Linux"
externalId = deviceName  #typically use serial #
config = { "lastUpdate":"Sept 29 09:13:56 PDT 2020","meaInterval":30,"gpsInterval":120}
deviceConfig = json.dumps(config)

def send_measurements():
	while True:
		measurements = []
		### GET YOUR DEVICE'S MEASUREMENTS HERE ###
		temperature = round(random.random()*100,2)
		pressure = round(random.random()*100,2)
		rssi = round(-90 + random.random()*10,2)
		cpu = round(20 + random.random()*10,2)
		memoryUsed = round(10 + cpu/10,2)
		### APPEND MEASUREMENTS ARRAY WITH ['measurementName','any-series-you-choose',float(measurement),'unit'] ###
		measurements.append(["Temperature","T1",temperature,"C"])
		measurements.append(["Pressure","P1",pressure,"mBar"])
		measurements.append(["c8y_SignalStrength", "rssi", rssi, "dBm"])
		measurements.append(["c8y_CPUMeasurement", "Workload", cpu, "%"])
		measurements.append(["c8y_MemoryMeasurement", "Used", memoryUsed, "MB"])
		### SEND MULTIPLE MEASUREMNTS WITH CUMULOCITY MEASUREMENT COLLECTION API ###
		headers = {'Content-type': 'application/json','Accept': 'application/vnd.com.nsn.cumulocity.measurementCollection+json'}
		url = myDevice.tenantURL + 'measurement/measurements'
		response = myDevice.httpHandler.http_request('POST',headers, url,'measurement_collection',measurements)
		print("Device measurements sent: " + str(response.status_code))

		### UPDATE INTERVAL IN CONFIG TAB ###
		config = json.loads(myDevice.deviceConfig)
		meaInterval = config["meaInterval"]
		time.sleep(meaInterval)		# Improve: will not restart thread immediately. Updates latch on next update, whenever that may be

def send_GPS():
	while True:
		altLongLat = []
		### GET YOUR DEVICE'S GPS HERE ###
		altLongLat = [0,-118.4741,34.0780]
		### END GPS CONFIG ###
		headers = {'Content-type': 'application/json','Accept': 'application/vnd.com.nsn.cumulocity.event+json'}
		url = myDevice.tenantURL + 'event/events'
		response = myDevice.httpHandler.http_request('POST',headers, url,'gps_event',altLongLat)
		print("GPS Event: "+str(response.status_code))
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		url = myDevice.tenantURL + 'inventory/managedObjects/'
		response = myDevice.httpHandler.http_request('PUT',headers, url,'gps_position',altLongLat)
		#status_code = myDevice.meac.update_gps_position(lat, lng)
		print("GPS Position Update: "+str(response.status_code))
		
		### UPDATE INTERVAL IN CONFIG TAB ###
		config = json.loads(myDevice.deviceConfig)
		gpsInterval = config["gpsInterval"]
		time.sleep(gpsInterval)

	#Use NCOS command cp.put('control/system/reboot') to restart

if __name__ == '__main__':

	#######################################################################################
	# Follow REST implementation flow from https://cumulocity.com/guides/device-sdk/rest/ #
	#######################################################################################

	pendingOps = []
	isDeviceRegistered = False
	myDevice = C8Y_Device(tenantURL, tenantId, deviceName, deviceType, externalId, deviceConfig)

	### Credentials Available? ###
	print("Reading credentials")
	areCredentialsAvailable = myDevice.read_credentials()
	if (areCredentialsAvailable == False):
		### 0. Request credentials ###
		myDevice.request_credentials(myDevice.deviceName) 

	### 1. Device Registered? ###  (If externalId exists it is registered)
	isDeviceRegistered = myDevice.get_ManagedObject_for_a_specific_externalId() 
	if isDeviceRegistered == False:
		### 2. Create Device ###
		isDeviceCreated = myDevice.create_device()
		### 3. Register Device ###
		if isDeviceCreated == True:
			isExternalIdCreated = myDevice.create_externalId()
			if isExternalIdCreated == True:
				isDeviceRegistered = True
	else:
		### 4. Update Device ### (Update properties. Not implemented yet)
		print("Updating Device")

	if isDeviceRegistered:
		print("Device " + str(myDevice.deviceId) + " is running")

		### 5. Discover Children ### (Not implemented yet)

		### 6. Finish operations and subscribe ### (Read 'pending.operations' and finish. Not implemented yet)
		myDevice.create_operations_handler()
		if len(pendingOps) != 0:
			print("Handling Operations")

		### Begin cycle phase ###
		myDevice.meaThread = Thread(target=send_measurements)
		myDevice.meaThread.daemon = True
		myDevice.meaThread.start()
		print("Measurements started")

		myDevice.gpsThread = Thread(target=send_GPS)
		myDevice.gpsThread.daemon = True
		myDevice.gpsThread.start()
		print("GPS events started")

	else:
		print("Done")

	while isDeviceRegistered:
		### Handle Operations loop on main thread ###
		myDevice.opsHandler.device_push_handshake()
		myDevice.opsHandler.device_push_subscribe()
		print("Subscribing to operations") 
		myDevice.opsHandler.device_push_connect()

