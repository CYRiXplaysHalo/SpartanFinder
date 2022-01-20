import urllib.request
import time
import json
from datetime import datetime
import socket
import sys
import re

def steamMCCscrape(currentPlayerOutFile, currentTimeStampOutFile, historicalOutFile):

	req2 = urllib.request.Request(
		url='https://steamcharts.com/app/976730/chart-data.json', 
		data=None, 
		headers={
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
		}
	)

	steam_stats = urllib.request.urlopen(req2)
	steam_stats_json = json.loads(steam_stats.read().decode('utf-8'))

	steam_total_count = steam_stats_json[len(steam_stats_json)-1][1]

	with open(historicalOutFile, "a") as myfile:
		myfile.write("\"" + datetime + "\",\""+ str(steam_total_count) + "\"\n")
	with open(currentPlayerOutFile, "w") as myfile:
		myfile.write(str(steam_total_count))
	with open(currentTimeStampOutFile, "w") as myfile:
			myfile.write(str(steam_stats_json[len(steam_stats_json)-1][0]/1000))
			
	return True