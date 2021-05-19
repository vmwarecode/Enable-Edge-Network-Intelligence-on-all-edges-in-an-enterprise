#!/usr/bin/env python3

import os
import scriptvars
import requests
import json

token = "Token %s" %(os.environ['VCO_Token'])
headers = {"Content-Type": "application/json", "Authorization": token}
vco_url = 'https://' + os.environ['VCO_URL'] + '/portal/rest/'
get_edges = vco_url + 'enterprise/getEnterpriseEdges'
edge_details = vco_url + 'edge/getEdge'
edge_attributes = vco_url + 'edge/updateEdgeAttributes'
edge_conf = vco_url + 'edge/getEdgeConfigurationStack'
conf_update = vco_url + 'configuration/updateConfigurationModule'
conf_mod_create = vco_url + 'configuration/insertConfigurationModule'


#function to enable ENI on the specified edge
def enableENI(targetedge):
	edge_attr = {	'id': targetedge,
					'_update': {'analyticsMode': 'SDWAN_ANALYTICS'}}
	#set analytics to "Application and Branch Analytics" in edge overview
	try:
		res = requests.post(edge_attributes, headers=headers, data=json.dumps(edge_attr))
	except Exception as e:
		print(e)
	#pull the edge configuration stack
	confcallparams = {'edgeId': targetedge}
	try:
		edgeconf = requests.post(edge_conf, headers=headers, data=json.dumps(confcallparams))
	except Exception as e:
		print(e)
	#convert to json
	edgeconfjson = edgeconf.json()
	confmoduleid = 0
	#Find the device settings configuration module and collect module ID and data object
	for module in edgeconfjson[0]['modules']:
		#print(str(module['name']) + str(module['id']))
		if module['name'] == 'deviceSettings':
			devsettings = module['data']
			confmoduleid = module['id']
		else:
			continue
	#enable analytics in each segment and set the source interface to GE3
	if confmoduleid != 0:
		#update existing config module
		print('modifying existing config module id ' + str(confmoduleid))
		for segment in devsettings['segments']:
			segment['analyticsSettings']['analyticsEnabled'] = True
			segment['analyticsSettings']['sourceInterface'] = 'GE3'
		#print(str(devsettings))
		edgeenableparams = {	"id": confmoduleid,
							  "_update": {
								"data": devsettings,
								"description": "",
								"name": "deviceSettings"
							  }
							}
		setpolicy = requests.post(conf_update, headers=headers, data=json.dumps(edgeenableparams))

	else:
		#print module not found
		print('Device Settings module not found for edge id ' + str(targetedge))
		

def main():
	#Retrieve all edges
		edgelistparams = {'with': ['analyticsMode']}
		try:
			edgelist = requests.post(get_edges, headers=headers, data=json.dumps(edgelistparams))
		except Exception as e:
			print(e)
		#convert to json
		edgelistjson = edgelist.json()
		#ignore edges identify edges with analytics set to "None"
		for edge in edgelistjson:
			edgeid = edge['id']
			edgename = edge['name']
			analyticsmode = edge['analyticsMode']
			#if edge analytics is "None", run function to turn it on, otherwise ignore it		
			if analyticsmode == 'SDWAN_ONLY':
				print("I'm gonna do stuff to edge '" + str(edgename) + "'")
				enableENI(edgeid)
			else:
				print("No action taken on edge '" + str(edgename) + "' since analytics mode is " + str(analyticsmode))
				continue
		

if __name__ == '__main__':
    main()