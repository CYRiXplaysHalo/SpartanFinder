import json
import http.client, urllib.request, urllib.parse, urllib.error, base64
import datetime
import time
import numpy as np
from datetime import timedelta
import pandas as pd
from os.path import listdir, isfile, join
import gzip
import shutil
import os

## Overview:
## - This script requires api access for twitch and for 343's h5 api feed.
## - It also requires a list of known halo 5 streamers.
## - How the script starts is by checking to see who on the list of twitch streamers
##	 are online, and using those known gamertags to check via 343 api their match history.
## - Using every match played in the past 15 minutes, the crawler then recursively goes
##	 through every match, adds all unique players to a list, then crawls those players,
##	 so we can get a reasonable proximation of how many unique gamertags were online
##	 during a 15 minute window.
## - Whenever the crawl is above 500, we send that to the web server.
## - The webserver then compared that number to what gamstat had for its h5 population count.
##	 Gamstat's xbox live numbers provided great calibration, but poor precision. As in,
##	 by its design it did a great job of telling you the approximate population of a game,
##   but its precision was I think at best in the hundreds if not thousands. Because of that,
##	 some logic was applied to use the crawler's output, gamstat's output, or some weighted
##   average of both.
## - The crawler had a tendency to succumb to a local maxima, typically when US streamers were
##	 not streaming very much. In those cases I did my best to not push those numbers as they 
##	 clearly were artifically low. Outside of that, the crawler tended to do a great job and would
##	 take a few hours to complete, resulting in a population number that was slightly stale 
##	 but accurate.

h5_api_key = ''
twitch_api_key = ''

def playerCrawl(player_count, player_list, player_name, match_id, match_list, recursion_level, populationLogOutFile, matchDetailsOutDirectory):
    try:
        ##Get the player's most recent matches
        try:
            match_history_conn = http.client.HTTPSConnection('www.haloapi.com')
            match_history_conn.request("GET", "/stats/h5/players/" + player_name.replace(' ','%20') + "/matches?%s" % match_history_params, "{body}", headers)
        except:
            time.sleep(3)
            match_history_conn = http.client.HTTPSConnection('www.haloapi.com')
            match_history_conn.request("GET", "/stats/h5/players/" + player_name.replace(' ','%20') + "/matches?%s" % match_history_params, "{body}", headers)
        match_history_response = match_history_conn.getresponse()
        match_history_raw = match_history_response.read()
        match_history_conn.close()
        match_history = json.loads(match_history_raw)

        if len(match_history['Results']) > 0:
            for i in range(0,len(match_history['Results'])):
                a = time.strptime(match_history['Results'][i]['MatchCompletedDate']['ISO8601Date'][:19], '%Y-%m-%dT%H:%M:%S')
                a = time.mktime(a)
                d = b - a
                minutes = int(d) / 60 
                if match_history['Results'][i]['Id']['MatchId'] != match_id and match_history['Results'][i]['Id']['MatchId'] not in match_list and minutes < 15 and minutes > 0:
                    game_to_use_index = i
                    match_id = match_history['Results'][i]['Id']['MatchId']
                    match_list.append(match_id)
                    match_date = match_history['Results'][i]['MatchCompletedDate']['ISO8601Date'][:19]
                    print("Found a match. " + str(match_history['Results'][i]['MatchCompletedDate']['ISO8601Date'][:19]))
                    break
            
            print("Currently at " + str(len(player_list)) + " players online. " + str(game_to_use_index))
            with open(populationLogOutFile, "a") as myfile:
                myfile.write("\"" + str(crawl_start) + "\",\""+ str(datetime.datetime.now())  + "\",\""+ str(len(player_list))  + "\",\""+  str(recursion_level) + "\"\n")
                
            ##If the match was within the past 30 minutes, get all of the players who participated and then send them through the crawler
            print("Yes. " + str(round(minutes,1)) + " minutes ago. " + match_date)
            #player_count += 1
            
            try:
                match_details_conn = http.client.HTTPSConnection('www.haloapi.com')
                match_details_conn.request("GET", "/stats/h5/matches/" + match_history['Results'][game_to_use_index]['Id']['MatchId'] + "/events", "{body}", headers)
            except:
                time.sleep(3)
                match_details_conn = http.client.HTTPSConnection('www.haloapi.com')
                match_details_conn.request("GET", "/stats/h5/matches/" + match_history['Results'][game_to_use_index]['Id']['MatchId'] + "/events", "{body}", headers)
            match_details_response = match_details_conn.getresponse()
            match_details_raw = match_details_response.read()
            match_details_conn.close()
            match_details = json.loads(match_details_raw)

			#Since we had to pull down a request that had each player in it, I chose the match details one with the thought of
			#saving off those files to preserve them. You can totally not do this.
            with open(matchDetailsOutDirectory + '\\' + str(match_history['Results'][game_to_use_index]['Id']['MatchId']) + '.json', 'w') as outfile:
                json.dump(match_details, outfile)
            
            match_player_list = []
			#assume all unique players do something in first 100 mins
            for j in range(1,100):#len(match_details['GameEvents'])):
                if 'Player' in match_details['GameEvents'][j] and match_details['GameEvents'][j]['Player']['Gamertag'] not in player_list and match_details['GameEvents'][j]['Player']['Gamertag'] != match_history['Results'][game_to_use_index]['Players'][0]['Player']['Gamertag']:
                    match_player_list.append(match_details['GameEvents'][j]['Player']['Gamertag'])
                    player_list.append(match_details['GameEvents'][j]['Player']['Gamertag'])
            
            player_count += len(match_player_list)
            for k in range(0,len(match_player_list)):
                recursion_level += 1
                playerCrawl(player_count, player_list, match_player_list[k], match_id, match_list, recursion_level, populationLogOutFile, matchDetailsOutDirectory)
    except:
        pass

    

def main(csvOfh5twitchStreamers, populationOutFile, populationLogOutFile, matchDetailsOutDirectory):

	headers = {
		# Request headers
		'Ocp-Apim-Subscription-Key': h5_api_key
	}

	match_history_params = urllib.parse.urlencode({
		'start': '0',
		'include-times': 'true',
	})

	while True:
		#Get the current time before the process starts, so we aren't accidentally shifting back 
		# the time measurement and infinitely counting players
		current_datetime_now = datetime.datetime.now() + timedelta(hours=4)
		b = time.strptime(current_datetime_now.isoformat()[:19], '%Y-%m-%dT%H:%M:%S')
		b = time.mktime(b)

		player_count = 0
		match_id = 0
		match_list = []

		twitch_list = pd.read_csv(csvOfh5twitchStreamers)  

		twitch_req = urllib.request.Request(
			url='https://api.twitch.tv/kraken/streams/?game=Halo%205%3A%20Guardians',
			data=None, 
			headers= {
			  'Accept': 'application/vnd.twitchtv.v5+json',
			  'Client-ID': twitch_api_key
			}
		)

		f = urllib.request.urlopen(twitch_req)
		raw_html = f.read().decode('utf-8')
		twitch_json = json.loads(raw_html)
		player_list = []
		#Start the crawler
		crawl_start = current_datetime_now
		print("Start crawl: " + str(crawl_start))
		recursion_level = 0
		for i in range(0,len(twitch_json['streams'])):
			if twitch_json['streams'][i]['channel']['name'] in list(twitch_list['url']):
				print(twitch_list[twitch_list['url'] == twitch_json['streams'][i]['channel']['name']]['gamertag'].item())
				player_name = twitch_list[twitch_list['url'] == twitch_json['streams'][i]['channel']['name']]['gamertag'].item()
				if len(player_list) > 0:
					player_list = player_list + [player_name]
				else:
					player_list = [player_name]
				playerCrawlplayerCrawl(player_count, player_list, player_name, match_id, match_list, recursion_level, populationLogOutFile, matchDetailsOutDirectory)
		print("Start crawl: " + str(crawl_start))
		print("End crawl: " + str(datetime.datetime.now() + timedelta(hours=4)))
		print("Final pop: " + str(len(player_list)))

		with open(populationLogOutFile, "a") as myfile:
			myfile.write("\"" + str(crawl_start) + "\",\""+ str(datetime.datetime.now() + timedelta(hours=4))  + "\",\""+  str(len(player_list)) + "\"\n")
		if len(player_list) > 500:
			with open(populationOutFile, "w") as myfile:
				myfile.write(str(len(player_list)))
			
		#Since the match detail files added up in total size, I compressed them individually after
		#a crawl completed
		onlyfiles = [f for f in listdir(matchDetailsOutDirectory) if isfile(join(matchDetailsOutDirectory, f))]
		for file in onlyfiles:
			print(file)
			try:
				with open(matchDetailsOutDirectory + "\\" + file, 'rb') as f_in:
					with gzip.open(newpath + "\\" + file + '.gz', 'wb') as f_out:
						shutil.copyfileobj(f_in, f_out)
				os.remove(matchDetailsOutDirectory + "\\" + file)
			except:
				print("Failed")
		if len(onlyfiles) < 50:
			time.sleep(360)
