import urllib.request
import time
import json
from datetime import datetime
import socket
import sys
import re

#RIP
def elDewritoScrape(currentPlayerOutFile, currentServerOutFile, historicalOutFile):
	req = urllib.request.Request(
		url='http://69.30.240.139/privateapi/getServers', 
		data=None, 
		headers={
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
		}
	)

	eldewrito_stats = urllib.request.urlopen(req)
	eldewrito_stats_json = json.loads(eldewrito_stats.read().decode('utf-8'))
	eldewrito_player_count = 0
	eldewrito_server_count = len(eldewrito_stats_json)
	for i in range(0,eldewrito_server_count):
		eldewrito_player_count += eldewrito_stats_json[i]['data']['numPlayers']

	with open(historicalOutFile, "a") as myfile:
		myfile.write("\"" + datetime + "\",\""+ str(eldewrito_player_count) + "\",\""+ str(eldewrito_server_count) + "\"\n")
	with open(currentServerOutFile, "w") as myfile:
		myfile.write(str(eldewrito_server_count))
	with open(currentPlayerOutFile, "w") as myfile:
		myfile.write(str(eldewrito_player_count))
		
	return True