import urllib.request
import time
import json
from datetime import datetime
import socket
import sys
import re

def projectCartographerScrape(currentPlayerOutFile, currentServerOutFile, historicalOutFile):

	req = urllib.request.Request(
		url='https://cartographer.online/live/server_list.php', 
		data=None, 
		headers={
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
		}
	)

	project_cartographer_stats = urllib.request.urlopen(req)
	project_cartographer_stats_json = json.loads(project_cartographer_stats.read().decode('utf-8'))
	project_cartographer_player_count = 0
	project_cartographer_server_count = len(project_cartographer_stats_json['servers'])
	for i in range(0,project_cartographer_server_count):
			req5 = urllib.request.Request(
				url='https://cartographer.online/live/server.php?xuid=' + project_cartographer_stats_json['servers'][i], 
				data=None, 
				headers={
				'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
				}
			)
			project_cartographer_server_stats = urllib.request.urlopen(req5)
			try:
				project_cartographer_server_stats_json = json.loads(project_cartographer_server_stats.read().decode('utf-8'))
				if 'dwFilledPrivateSlots' in project_cartographer_server_stats_json:
					project_cartographer_player_count += int(project_cartographer_server_stats_json['dwFilledPublicSlots']) + project_cartographer_server_stats_json['dwFilledPrivateSlots']
				else:
					project_cartographer_player_count += int(project_cartographer_server_stats_json['dwFilledPublicSlots'])
			except json.decoder.JSONDecodeError:
				continue

	with open(historicalOutFile, "a") as myfile:
		myfile.write("\"" + datetime + "\",\""+ str(project_cartographer_player_count) + "\",\"" + str(project_cartographer_server_count) + "\"\n")
	with open(currentPlayerOutFile, "w") as myfile:
		myfile.write(str(project_cartographer_player_count))
	with open(currentServerOutFile, "w") as myfile:
		myfile.write(str(project_cartographer_server_count))

	return True