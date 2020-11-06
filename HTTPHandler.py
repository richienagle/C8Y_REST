##################  HTTPHandler.py  ############################
# HTTPHandler is a class used to handle http
# requests, and provides a means to handle
# errors gracefully. 
# 
# Cumulocity REST API postman collection can be found at:
#
#
# Cumulocity related error codes can be found at:
# https://www.cumulocity.com/guides/reference/rest-implementation/#http-usage
# 
################################################################
import requests	
from datetime import datetime
import json

class HTTPHandler:

	deviceId = None

	def __init__(self, tenantURL,tenantId,deviceId,deviceType,externalId,credentials):
		self.tenantURL = tenantURL
		self.tenantId = tenantId
		self.deviceId = deviceId
		self.deviceType = deviceType
		self.externalId = externalId
		self.credentials = credentials
		self.bootstrapCredentials = ["devicebootstrap","Fhdt1bb1f"]

	def http_request(self, method, headers, url, requestType, data):

		retryCount = 0

		if requestType == 'measurement_collection':
			data = self.create_measurements_body(data)
		elif requestType == 'gps_event':
			data = self.create_gps_event(data)
		elif requestType == 'gps_position':
			url = url + str(self.deviceId)
			data = self.update_gps_position(data)
		elif requestType == 'get_device_credentials':
			self.credentials = self.bootstrapCredentials

		try:
			#print(json.dumps(data))
			if method == 'POST':
				response = requests.post(url = url, data = json.dumps(data), headers=headers, auth = (self.tenantId+"/"+self.credentials[0],self.credentials[1]))
			elif method == 'PUT':
				response = requests.put(url = url, data = json.dumps(data), headers=headers, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
			elif method == 'GET':
				response = requests.get(url = url, data = json.dumps(data), headers=headers, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))

		except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
		except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
			# Options: buffer data, restart connectivity
			# HTTPSConnectionPool(host='richardnagle.us.cumulocity.com', port=443): Max retries exceeded with url: /measurement/measurements (Caused by SSLError(SSLError("bad handshake: SysCallError(-1, 'Unexpected EOF')")))
		except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
			# Options: set up for a retry, or continue in a retry loop
		except requests.exceptions.RequestException as err:
			print ("Report Error to Cumulocity admin: ",err)
			
		return response


	def http_file_request(self, method, headers, url, requestType, data, file):

		retryCount = 0

		try:
			response = requests.request("POST", url, headers=headers, data = data, files = file, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))
			#response = requests.request("POST", url, headers=headers, data = payload, files = files, auth = (self.tenantId+"/"+self.credentials[0], self.credentials[1]))

		except requests.exceptions.HTTPError as errh:
			print ("Http Error:",errh)
		except requests.exceptions.ConnectionError as errc:
			print ("Error Connecting:",errc)
			# Options: buffer data, restart connectivity
			# HTTPSConnectionPool(host='richardnagle.us.cumulocity.com', port=443): Max retries exceeded with url: /measurement/measurements (Caused by SSLError(SSLError("bad handshake: SysCallError(-1, 'Unexpected EOF')")))
		except requests.exceptions.Timeout as errt:
			print ("Timeout Error:",errt)
			# Options: set up for a retry, or continue in a retry loop
		except requests.exceptions.RequestException as err:
			print ("Report Error to Cumulocity admin: ",err)
			
		return response


	def create_measurements_body(self, measurements):
		timestamp = (datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'))
		myid = str(self.deviceId)
		#data = {"measurements": [{"c8y_Temperature": {"T": {"value": 25.9,"unit": "C" }},"time":timestamp,"source": {"id":"12825620" },"type": "c8y_Temperature"},{"c8y_Humidity": {"RH": { "value": 58.9,"unit": "RH" }},"time":timestamp, "source": {"id":"12825620" }, "type": "c8y_Humidity"}]}
		data = {"measurements": []}
		for i in measurements:
			measurement = {i[0]: {i[1]: {"value": i[2],"unit": i[3]}},"time":timestamp,"source": {"id":myid },"type": i[0]}
			data["measurements"].append(measurement)
		#print(json.dumps(data))
		return data

	def create_gps_event(self,altLongLat):
		timestamp = (datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'))
		myid = str(self.deviceId)
		data = {"c8y_Position": {"alt": altLongLat[0], "lng": altLongLat[1], "lat": altLongLat[2]},"source": {"id":myid },"type": "c8y_LocationUpdate","text": "GPS Update","time": timestamp}
		return data

	def update_gps_position(self,altLongLat):
		timestamp = (datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.000Z'))
		data = {"c8y_Position": {"alt": altLongLat[0], "lng": altLongLat[1], "lat": altLongLat[2]}}
		return data




