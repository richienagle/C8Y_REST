
Note2:  
- This is for python3. Python3 may likely installed on your computer, but if not follow installation instructions: https://www.python.org/
- The Python 'requests' library (https://pypi.org/project/requests/2.7.0/) will need to be added in order for this to run.
- A free trial can be started here https://www.softwareag.cloud/site/product/cumulocity-iot.html#/

### Directory Structure ###
C8Y_REST/
- C8Y_Demo.py 
customize info in lines 12-17 for your Cumulocity tenant and device name.  
- C8Y_Device.py 					
Cumulocity device class, haddles registration, credentials, and externalId 
- HTTPHandle.py		
functions to send measurements and events
- Device_Operations_Handler.py 	
handles long polling subscription and operations
- Cumulocity API.postman_collection.json
Postman collection for REST APIs
- device.properties				
credentials created upon registration, if device is deleted then delete this file and re-run REST_Demo.py
- info.log						
generic text file, read only to show log retreval operation

### How to use ###
1. Change lines 12 & 16 of GatewayDemo.py, the externalId on line 16 must be unique, only one of these can exist among devices in Cumulocity.
2. To execute, install 'requests' library and then run:
	$ python3 C8Y_Demo.py
3. Go to https://<your tenant>.us.cumulocity.com/apps devicemanagement/index.html#/deviceregistration and register the device name that's in line 15 of C8Y_Demo.py
4. It will register the device and externalId, and update property info. Customized properties can be added.
5. In a few seconds, the device will appear in Device Management -> All Devices https://<your tenant>.us.cumulocity.com/apps/devicemanagement/index.html#/device
6. Supports operations: 
	- Restart
	- Firmware Upgrade
	- Configuration update (Update numerical variables only in config text)
	- Log file retreval

### Useful links ###
	- More simple examples: https://github.com/SoftwareAG/cumulocity-iot-examples
	- https://cumulocity.com/guides/device-sdk/rest/
	- https://cumulocity.com/guides/reference/rest-implementation/#http-usage
	- https://cumulocity.com/guides/reference/rest-implementation/#rest-usage
	- API reference: https://cumulocity.com/guides/reference/
