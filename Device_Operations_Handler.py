import requests
import json
import time
import os, fnmatch
from datetime import datetime
import re
import sys

class Device_Operations_Handler:

	def __init__(self, myDevice,tenantURL,tenantId,deviceId,credentials,clientId,timeout):
		self.myDevice = myDevice			#just added, remove and rename other info
		self.tenantURL = tenantURL
		self.tenantId = tenantId
		self.deviceId = deviceId
		self.credentials = credentials
		self.clientId = 0
		self.timeout = 60000

	def device_push_handshake(self):
		url = self.tenantURL+"devicecontrol/notifications"
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		body = [{"version":"1.0","minimumVersion":"0.9","channel":"/meta/handshake","supportedConnectionTypes":["long-polling"],"advice":{"timeout":self.timeout,"interval":0}}]
		response = self.myDevice.httpHandler.http_request('POST',headers,url,'device_push_handshake',body)
		#r = requests.post(url = url, data = json.dumps(body), headers=headers, auth = (self.tenantId+"/"+self.credentials [0], self.credentials [1]))
		if response.status_code != 200:
			print (response.status_code)
			print ('Could not initiate real time notifications.  Please contact your Cumulocity Admin')
			return False
		else:
			resp = response.json()
			x = resp[0].get('clientId')
			self.clientId = x
			return True

	def device_push_subscribe(self):
		url = self.tenantURL+"devicecontrol/notifications"
		myDeviceId = "/"+str(self.deviceId)
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		body = [{"id": "2","channel":"/meta/subscribe","subscription":self.deviceId,"clientId":self.clientId}]
		#r = requests.post(url = url, data = json.dumps(body), headers=headers, auth = (self.tenantId+"/"+self.credentials [0], self.credentials [1]))
		response = self.myDevice.httpHandler.http_request('POST',headers,url,'device_push_subscribe',body)
		#if r.status_code != 200:
			#print (r.status_code)
			#print ('Could not subscribe to real time notifications.  Please contact your Cumulocity Admin')
		#	return False
		#else:
			#print(url + " - Subscribe - " + str(r.status_code))
		#	return True

	def device_push_connect(self):
		url = self.tenantURL+"devicecontrol/notifications"
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		body = [{"channel":"/meta/connect","connectionType":"long-polling","clientId":self.clientId}]
		#r = requests.post(url = url, data = json.dumps(body), headers=headers, auth = (self.tenantId+"/"+self.credentials [0], self.credentials [1]))
		response = self.myDevice.httpHandler.http_request('POST',headers,url,'device_push_connect',body)
		#print(url + " - Connect - " + str(r.status_code))
		if response.status_code != 200:
			print (response.status_code)
			print ('Could not connect to real time notifications or timed out.  Please contact your Cumulocity Admin')
		resp = response.json()
		opId = resp[0]['data'].get('id')
		self.save_opid(opId,resp)
		data = resp[0].get('data')
		self.handle_operation(opId,data)

	def handle_operation(self,opId,data):

		self.update_operation_status(opId, "EXECUTING")

		desc = data['description']
		print(desc)

		if re.match(r'Configuration update',desc):
			print(json.dumps(data['c8y_Configuration']))
			successCheck = self.configuration_update(opId,data)
		elif re.match(r'Restart device',desc):
			print(json.dumps(data['c8y_Restart']))
			successCheck = self.restart_device(opId,data)
		elif re.match(r'Update firmware',desc):
			print(json.dumps(data['c8y_Firmware']))
			successCheck = self.firmware_update(opId,data)
		elif re.match(r'Update software:',desc):
			print(json.dumps(data['c8y_Software']))
			#successCheck = self.software_update(opId,data)
		elif re.match(r'Log file request',desc):
			print(json.dumps(data['c8y_LogfileRequest']))
			successCheck = self.log_file_request(opId,data)
		elif re.match(r'Execute shell command:',desc):
			print(json.dumps(data['c8y_Command']['text']))
			#successCheck = self.command_request(opId,data)
		else:
			print('Operation Not Handled')

		# Add conditional check on success
		self.update_operation_status(opId, "SUCCESSFUL")

	def update_operation_status(self,opId, opState):
		# opState = [EXECUTING, SUCCESSFUL,FAILED]
		if re.match(r"SUCCESSFUL", opState):
			self.delete_opid(opId)
		#else:
			#body = {"status": "FAILED","failureReason": "Could not handle operation"}
		url = self.tenantURL+"devicecontrol/operations/" + opId
		body = {"status": opState}
		headers = {'Content-type': 'application/json','Accept': 'application/vnd.com.nsn.cumulocity.operation+json'}
		#r = requests.put(url = url, data = json.dumps(body), headers=headers, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
		response = self.myDevice.httpHandler.http_request('PUT',headers,url,'update_operation_status',body)
		print("Status: " + opState + " - " + str(response.status_code))
		#resp = response.json()

	def delete_opid(self,opid):
		os.remove('operations.properties')

	def save_opid(self,opId,resp):
		file = open('operations.properties', 'w')
		file.write(opId)
		file.close()

	def configuration_update(self,operationId,response):
		#print(response['c8y_Configuration']['config'])
		### need to check if valid json or will crash ###
		self.myDevice.deviceConfig = response['c8y_Configuration']['config']

		config = json.loads(response['c8y_Configuration']['config'])
		meaInterval = config['meaInterval']
		gpsInterval = config['gpsInterval']
		timestamp = (datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'))
		data = {"lastUpdate": timestamp, "meaInterval": meaInterval, "gpsInterval": gpsInterval}
		configString = json.dumps(data)
		self.update_configuration_properties(configString)
		return True

	def update_configuration_properties(self,configString):
		url = self.tenantURL+"inventory/managedObjects/" + str(self.myDevice.deviceId)
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		body = {"c8y_Configuration": {"config":configString}}
		response = self.myDevice.httpHandler.http_request('PUT',headers,url,'update_configuration_properties',body)
		#r = requests.put(url = url, data = json.dumps(body), headers=headers, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
		#print("Updating unique agent properties: " + deviceId + " " + str(r.status_code))
		#resp = response.json()

	def restart_device(self,operationId,response):
		#print(response['description'])
		strToSend = 'Insert OS reset commend in code here'
		print(strToSend)
		print('#####################')
		print('# Restarting Device #')
		print('#####################')
		time.sleep(3)
		#cp.put('control/system/reboot')
		return True

	def log_file_request(self,opId,data):
		print(data['description'])
		#print("data to send back in operation: " + str(data['c8y_LogfileRequest']))
		logInfo = data['c8y_LogfileRequest']
		#######################
		#upload multipart binary
		#######################
		url = self.tenantURL + "inventory/binaries"
		headers = {'Content-Type': 'multipart/form-data'}
		payload = {'object': '{"name":"Info.log","type":"text/plain"}','filesize': '19017'} 
		files = [('file', open('Info.log','rb'))]
		response = self.myDevice.httpHandler.http_file_request('POST',headers,url,'log_file_request',payload, files)
		#response = requests.request("POST", url, headers=headers, data = payload, files = files, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
		fileLocation = response.headers['Location']
		#############################
		# put binary loc in success
		#############################
		logInfo['file'] = fileLocation	#add file location

		url = self.tenantURL+"devicecontrol/operations/" + opId
		#print(url)
		body = {"status": "SUCCESSFUL"}
		body['c8y_LogfileRequest'] = logInfo
		headers = {'Content-type': 'application/json','Accept': 'application/vnd.com.nsn.cumulocity.operation+json'}
		response = self.myDevice.httpHandler.http_request('PUT',headers,url,'log_file_request',body)
		#r = requests.put(url = url, data = json.dumps(body), headers=headers, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
		#print("Log file Op Status: " + str(r.status_code))
		return True

	def firmware_update(self,operationId,response):
		print(response['description'])
		fwURL = response['c8y_Firmware']['url']
		fwName = response['c8y_Firmware']['name']
		fwVersion = response['c8y_Firmware']['version']
		print('firmware url: ' + fwURL)
		#downloadFirmware(fwURL,fwName,fwVersion)
		self.update_fw_properties(fwName,fwVersion)
		return True

	def update_fw_properties(self,fwName,fwVersion):
		url = self.tenantURL+"inventory/managedObjects/" + str(self.myDevice.deviceId)
		headers = {'Content-type': 'application/json','Accept': 'application/json'}
		body = {"c8y_Firmware": {"name": fwName,"version": fwVersion}}
		response = self.myDevice.httpHandler.http_request('PUT',headers,url,'update_fw_properties',body)
		#r = requests.put(url = url, data = json.dumps(body), headers=headers, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
		#print("Updating unique agent properties: " + deviceId + " " + str(r.status_code))
		#resp = response.json()
