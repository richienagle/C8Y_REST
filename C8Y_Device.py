import requests 				# for HTTP https://pypi.org/project/requests/
import json						# for json parsing and formatting
from datetime import datetime	# for date & time formatting in HTTP POSTs
import time						# for time.sleep() functionality
import os
import fnmatch
from Device_Operations_Handler import Device_Operations_Handler
from HTTPHandler import HTTPHandler
import sys

class C8Y_Device:

	httpHandler = None
	opsHandler = None
	meaThread = None # Thread to run periodic measurements
	gpsThread = None # Thread to run periodic gps events

	def __init__(self, tenantURL,tenantId,deviceName,deviceType,externalId,deviceConfig):
		self.tenantURL = tenantURL
		self.tenantId = tenantId
		self.deviceName = deviceName
		self.deviceType = deviceType
		self.deviceId = 0
		self.externalId =  externalId
		self.deviceConfig =  deviceConfig
		self.bootstrapCredentials = ["devicebootstrap","Fhdt1bb1f"]
		self.credentials = []
		self.fileHandle = None
		self.create_http_handler()

	def create_http_handler(self):
		self.httpHandler = HTTPHandler(self.tenantURL,self.tenantId,self.deviceId,self.deviceType,self.externalId,self.credentials)

	def create_operations_handler(self):
		self.opsHandler = Device_Operations_Handler(self,self.tenantURL,self.tenantId,self.deviceId,self.credentials,0,60000)
		#return True

	def read_credentials(self):
		credentials = []
		currentDirectory = os.getcwd()
		for file in os.listdir(currentDirectory):
			if fnmatch.fnmatch(file,'device.properties'):
				with open('device.properties') as credentialsFile:
					# 'device.properties' file should exist in this directory and contain 2 separate lines:
					# username
					# password
					line = credentialsFile.readline()
					cnt = 1
					while line:
						credentials.append(line.strip())
						line = credentialsFile.readline()
						cnt += 1
					credentialsFile.close()
				self.credentials = credentials
				#print(self.credentials[0]+ "\n" + self.credentials[1])
		credentialsAvailable = False
		if len(self.credentials) != 0:
			credentialsAvailable = True
			self.httpHandler.credentials = credentials
		return credentialsAvailable

	def request_credentials(self,deviceName):
		credentials = []
		while len(credentials) == 0:
			time.sleep(5)
			credentials = self.get_device_credentials(deviceName)
			if len(credentials) != 0:
				# Implement https://stackoverflow.com/questions/14636290/secure-credential-storage-in-python
				print("Recieved new device credentials")
				file = open('device.properties', 'w')
				file.write(credentials[0]+"\n")
				file.write(credentials[1])
				file.close()
		self.httpHandler.credentials = credentials #update
		self.credentials = credentials
		#return credentials

	def get_device_credentials(self,deviceName):
		print("Requesting credentials for device: " + deviceName)
		body = {"id" : deviceName}
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		url = self.tenantURL + 'devicecontrol/deviceCredentials'
		response = self.httpHandler.http_request('POST',headers,url,'get_device_credentials',body)
		resp = response.json()
		credentials = []
		if response.status_code == 201:
			credentials.append(resp['username'])
			credentials.append(resp['password'])
		else:
			stringToLog = "Please register & accept " + self.deviceName + " at:\n" + self.tenantURL + "apps/devicemanagement/index.html#/deviceregistration"
			print(stringToLog)
		#self.credentials = credentials
		return credentials


	def get_ManagedObject_for_a_specific_externalId(self):
		body = ""
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		url =  self.tenantURL + 'identity/externalIds/' + self.deviceType + "/" + self.externalId
		response = self.httpHandler.http_request('GET',headers,url,'get_external_Id',body)
		isDeviceRegistered = False
		if response.status_code == 200:
			resp = response.json()
			deviceId = resp['managedObject']['id']
			isDeviceRegistered = True
		elif response.status_code == 401:
			print("Device no longer exists at " + self.tenantURL + ". Remove device.properties file in local directory")
			sys.exit()
		else:
			deviceId = 0
		self.deviceId = deviceId
		self.httpHandler.deviceId = deviceId
		return isDeviceRegistered

	def create_device(self):
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		url = self.tenantURL + "inventory/managedObjects"
		body = {"name": self.deviceName,"type": self.deviceType,"c8y_IsDevice": {},"com_cumulocity_model_Agent": {},"c8y_SupportedOperations": [ "c8y_Restart", "c8y_Configuration", "c8y_SoftwareList", "c8y_Firmware", "c8y_UploadConfigFile", "c8y_DownloadConfigFile", "c8y_SendConfiguration", "c8y_Command", "c8y_LogfileRequest"],"c8y_Hardware": {"revision": "1.0","model": "IBR 1700","serialNumber": self.externalId},"c8y_Configuration": {"config": self.deviceConfig},"c8y_Mobile": {"imei": "8611450130921231","cellId": "4904-A496","iccid": "89490200000876635112"},"c8y_Firmware": {"name": "Firmware","version": "1.0.0"},"c8y_Software": {"agent_Version": "agent_rev1.0"},"c8y_SupportedLogs": ["Info Log"]}
		response = self.httpHandler.http_request('POST',headers,url,'create_device',body)
		if response.status_code != 201:
			print ('Could not create Device: ' + self.deviceName)
			return False
		resp = response.json()
		print('Created device with id: ' + resp['id'])
		deviceId = resp['id']
		self.deviceId = deviceId
		self.httpHandler.deviceId = deviceId
		return True

	def create_externalId(self):
		headers = {'Content-Type': 'application/vnd.com.nsn.cumulocity.externalId+json','Accept': 'application/vnd.com.nsn.cumulocity.externalId+json'}
		url = self.tenantURL + "identity/globalIds/" + str(self.deviceId) + "/externalIds"
		data = {"externalId": self.externalId,"type": self.deviceType}
		r = requests.post(url = url, data = json.dumps(data), headers=headers, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
		if r.status_code != 201:
			print('Could not create externalId for device: ' + str(self.deviceId))
			#print(r.status_code)
			return False
		else:
			resp = r.json()
			print('Created externalId: ' + resp['externalId'])
		return True

