import urllib.request
import time
import json
from datetime import datetime
import socket
import sys
import re

def halo1PCscrape(currentPlayerOutFile, currentServerOutFile, historicalOutFile):

	req = urllib.request.Request(
		url='https://www.gametracker.com/games/halo/', 
		data=None, 
		headers={
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
		}
	)

	f = urllib.request.urlopen(req)
	raw_html = f.read().decode('utf-8')

	server_count = raw_html[raw_html.find("Servers:"):]
	server_count = server_count[server_count.find("/search/halo/")+15:]
	server_count = server_count[:server_count.find("</a>")].replace("\n","").replace("\t","")


	player_count = raw_html[raw_html.find("Players:"):]
	player_count = player_count[player_count.find("item_float_right")+19:]
	player_count = player_count[:player_count.find("</div>")].replace("\n","").replace("\t","")

	with open(historicalOutFile, "a") as myfile:
		myfile.write("\"" + datetime + "\",\""+ str(server_count) + "\",\"" + str(player_count) + "\"\n")
	with open(currentServerOutFile, "w") as myfile:
		myfile.write(str(server_count))
	with open(currentPlayerOutFile, "w") as myfile:
		myfile.write(str(player_count))
		
	return True