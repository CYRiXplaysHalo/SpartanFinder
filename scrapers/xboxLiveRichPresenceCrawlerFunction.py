import sys
import json
import sqlite3
from datetime import datetime, timezone
import datetime
import time
import datetime as DT
import pandas as pd
import ftplib

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.common.exceptions import AuthenticationException

##	I set up a db to track users and their meta data. 
##	CREATE TABLE players
##	             (xuid INT PRIMARY KEY,
##	             friendslist TEXT,
##	             last_gm TEXT,
##	             last_device TEXT,
##	             last_seen datetime,
##	             update_dt datetime
##	             )
conn = sqlite3.connect(dbFile)

##	This script uses a a deprecated version of xbox-webapi-python:
##	https://github.com/OpenXbox/xbox-webapi-python/tree/c9c73f61faa77b6954fe9f7375bae21460bc2bd6
##
##	This version of xbox-webapi-python used a more simplistic method for obtaining
##	an authentication token, and it only needed to be updated every two weeks or so.
##	The newer one is more involved and invovled writing new code, so I never updated
##	as this version never stopped working for me.
##
##	At a high level what we are doing is keeping a databse of known halo players, and 
##	recursively going through each one of their friends lists to see if any of their
##	friends are playing a Halo game. For each player we check what their presence and
##	rich presence is as that tells us which specific game they are playing in MCC as well
##	as what precisely they are doing. That way at the end of each crawl we have a good sample
##	of who is playing which halo title, and what they are currently doing.


##	Just a simple class to keep track of stats for each halo game
class Game:
  def __init__(self, title, platform, population, richPresenceList):
    self.title = title
    self.platform = platform
    self.population = population
    self.richPresenceList = richPresenceList

##	This is the function that gets recursively called as we go through
##	each player's friendlist
def getPlayerInfo(xuid, processed_friendslist, recursion_level):

    # Get friendslist
    c = conn.cursor()
    c.execute("SELECT friendslist FROM players where xuid = '" + xuid + "'")
    friendlist_sql = c.fetchall()
	
	#If we have a friendslist for them, prase it
    if len(friendlist_sql) > 0 and 'people' in str(friendlist_sql[0])[2:-3]:
        friendslist_json = json.loads(str(friendlist_sql[0])[2:-3])
	#If we don't, fetch it
    else:
        friendslist = xbl_client.people.get_friends_by_xuid(xuid)
        friendslist_json = json.loads(friendslist.text)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO players (xuid, friendslist, last_gm, last_device, last_seen, update_dt) values ('" + xuid + "','" + str(friendslist.text) + "',NULL,NULL,NULL,'" + str(datetime.datetime.now()) + "')")
        conn.commit()
	
	#Can't remember original purpose of this
    if xuid not in processed_friendslist:
        friendslist_xuids = [xuid]
    else:
        friendslist_xuids = [xuid]

	#If the friendlist json returns friends, add them the main list
    if 'people' in friendslist_json:
        for i in range(0,len(friendslist_json['people'])):
            friendslist_xuids.append(friendslist_json['people'][i]['xuid'])
            
		#get presence of all friends
        presence = xbl_client.presence.get_presence_batch(friendslist_xuids, online_only=False, presence_level='all')
        presence_json = json.loads(presence.text)

		#parse presence of all friends
        for i in range(0,len(presence_json)):
            if presence_json[i]['state'] == 'Online' and presence_json[i]['xuid'] not in processed_friendslist:
                processed_friendslist.append(presence_json[i]['xuid'])
						
				#If there is richPresence, let's do something with it
                j = len(presence_json[i]['devices']) - 1
                if 'activity' in presence_json[i]['devices'][j]['titles'][0] and ('Halo' in presence_json[i]['devices'][j]['titles'][0]['name'] or 'MCC' in presence_json[i]['devices'][j]['titles'][0]['name']) and 'richPresence' in presence_json[i]['devices'][j]['titles'][0]['activity']:

					#Update presence for player in db
                    c = conn.cursor()
                    c.execute("UPDATE players SET last_gm = '" + str(presence_json[i]['devices'][j]['titles'][0]['name']) + "', last_device = '" + str(presence_json[i]['devices'][j]['type']) + "', last_seen = '" + str(datetime.datetime.now()) + "', update_dt = '" + str(datetime.datetime.now()) + "' where xuid = '" + str(presence_json[i]['xuid']) + "';") 
                    conn.commit()

					#Add halo titles dynamically and save richPresence
                    gameInList = False
                    richPresenceInList = False
                    for k in range (0,len(game_list)):
                      if game_list[k].title == str(presence_json[i]['devices'][j]['titles'][0]['name']) and game_list[k].platform ==  str(presence_json[i]['devices'][j]['type']):
                        gameInList = True
                        game_list[k].population = game_list[k].population + 1
                        for m in range(0,len(game_list[k].richPresenceList)):
                          if game_list[k].richPresenceList[m][0] == str(presence_json[i]['devices'][j]['titles'][0]['activity']['richPresence']):
                            richPresenceInList = True
                            game_list[k].richPresenceList[m][1] = game_list[k].richPresenceList[m][1] + 1
                    if gameInList == False:
                      new_game = Game(str(presence_json[i]['devices'][j]['titles'][0]['name']), str(presence_json[i]['devices'][j]['type']),1,[])
                      game_list.append(new_game)
                    if richPresenceInList == False:
                      new_presence = [str(presence_json[i]['devices'][j]['titles'][0]['activity']['richPresence']),1]
                      for k in range (0,len(game_list)):
                        if game_list[k].title == str(presence_json[i]['devices'][j]['titles'][0]['name']) and game_list[k].platform ==  str(presence_json[i]['devices'][j]['type']):
                          game_list[k].richPresenceList.append(new_presence)
                            
                    recursion_level += 1
                    if recursion_level < 999:
                        getPlayerInfo(str(presence_json[i]['xuid']), processed_friendslist, recursion_level)
                    else:
                        leftover_xuids.apped(str(presence_json[i]['xuid']))
						
				#If no rich presence, just save game
                elif 'Halo' in presence_json[i]['devices'][j]['titles'][0]['name']:
                    c = conn.cursor()
                    c.execute("UPDATE players SET last_gm = '" + str(presence_json[i]['devices'][j]['titles'][0]['name']) + "', last_device = '" + str(presence_json[i]['devices'][j]['type']) + "', last_seen = '" + str(datetime.datetime.now()) + "', update_dt = '" + str(datetime.datetime.now()) + "' where xuid = '" + str(presence_json[i]['xuid']) + "';") 
                    conn.commit()
                    
                    gameInList = False
                    for k in range (0,len(game_list)):
                      if game_list[k].title == str(presence_json[i]['devices'][j]['titles'][0]['name']) and game_list[k].platform ==  str(presence_json[i]['devices'][j]['type']):
                        gameInList = True
                        game_list[k].population = game_list[k].population + 1
                    if gameInList == False:
                      new_game = Game(str(presence_json[i]['devices'][j]['titles'][0]['name']), str(presence_json[i]['devices'][j]['type']),1,[])
                      game_list.append(new_game)
                    recursion_level += 1
                    if recursion_level < 999:
                        getPlayerInfo(str(presence_json[i]['xuid']), processed_friendslist, recursion_level)
                    else:
                        leftover_xuids.apped(str(presence_json[i]['xuid']))
                else:
                    c = conn.cursor()
                    c.execute("UPDATE players SET update_dt = '" + str(datetime.datetime.now()) + "' where xuid = '" + str(presence_json[i]['xuid']) + "';") 
                    conn.commit()

def main(dbFile, authToken, richPresenceOutputFile, richPresenceLogFile, FTP_SERVER,FTP_USER,FTP_PW):

	try:
	  auth_mgr = AuthenticationManager.from_file(authToken)
	except FileNotFoundError as e:
	  print(
		'Failed to load tokens from \'{}\'.\n'
		'ERROR: {}'.format(e.filename, e.strerror)
	  )
	  sys.exit(-1)

	try:
	  auth_mgr.authenticate(do_refresh=True)
	except AuthenticationException as e:
	  print('Authentication failed! Err: %s' % e)
	  sys.exit(-1)

	xbl_client = XboxLiveClient(auth_mgr.userinfo.userhash, auth_mgr.xsts_token.jwt, auth_mgr.userinfo.xuid)

	#At this point we have loaded the xbl authentication token and connected to the xbox-webapi-python api.

	game_list = []
	leftover_xuids = []

	#I tracked how long it took for debugging context
	today = DT.date.today()
	week_ago = today - DT.timedelta(days=7)
	now = str(datetime.datetime.now())
	
	#Get all xuids in db
	c = conn.cursor()
	c.execute("select xuid from players where date(last_seen)>date('" + week_ago.strftime('%Y-%m-%d') + "');")
	plist = pd.DataFrame(c.fetchall())
	plist = list(plist[0])

	#go through all of them and recursively get presence and richPresence, but
	#also keep a running list of xuid's used so we don't process them multiple times
	#and also keep a list of recursion levels so python stays happen
	processed_friendslist = []
	for p in plist:
	  recursion_level = 1
	  if str(p) not in processed_friendslist:
		  print(p)
		  try:
			  getPlayerInfo(str(p), processed_friendslist, recursion_level)
		  except:
			  continue

	#Just for debug context
	print(datetime.datetime.now())


	rp_breakdown_current = richPresenceOutputFile	#File used to send to spartanfinder
	rp_breakdown_historical = richPresenceLogFile	#historical log

	#Initiailize output files
	with open(rp_breakdown_current, 'w') as myfile:
		myfile.write("Title,Platform,TitlePopulation,RichPresence,RichPresenceCount,MCCGame,MCCMode,MCCCampaignDifficulty,MCCMap\n")
	with open(rp_breakdown_historical, 'w') as myfile:
		myfile.write("Title,Platform,TitlePopulation,RichPresence,RichPresenceCount,MCCGame,MCCMode,MCCCampaignDifficulty,MCCMap\n")
		
	#Parse games and their rich presences to output them.
	for i in range(0,len(game_list)):
	  if game_list[i].richPresenceList != []:
	  
		print(str(game_list[i].title) + "," + str(game_list[i].platform) + "," + str(game_list[i].population))
		for j in range(0,len(game_list[i].richPresenceList)):
		
			#If it's an MCC row, parse out the individual games
			MCCGame = ''
			MCCMode = ''
			MCCCampaignDifficulty = ''
			MCCMap = ''
			if 'Master' in game_list[i].title:
				if 'H: CE:' in str(game_list[i].richPresenceList[j][0]):
					MCCGame = 'H1'
				elif 'H: R:' in str(game_list[i].richPresenceList[j][0]):
					MCCGame = 'HR'
				elif 'H2:' in str(game_list[i].richPresenceList[j][0]):
					MCCGame = 'H2'
				elif 'H2A:' in str(game_list[i].richPresenceList[j][0]):
					MCCGame = 'H2A'
				elif 'H3:' in str(game_list[i].richPresenceList[j][0]):
					MCCGame = 'H3'
				elif 'H4:' in str(game_list[i].richPresenceList[j][0]):
					MCCGame = 'H4'
				elif 'ODST' in str(game_list[i].richPresenceList[j][0]):
					MCCGame = 'ODST'

				if 'Campaign Co-op' in str(game_list[i].richPresenceList[j][0]) or 'Campaign' in str(game_list[i].richPresenceList[j][0]) or 'Mission' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Campaign'
					if 'Easy' in str(game_list[i].richPresenceList[j][0]):
						MCCCampaignDifficulty = 'Easy'
					elif 'Normal' in str(game_list[i].richPresenceList[j][0]):
						MCCCampaignDifficulty = 'Normal'
					elif 'Heroic' in str(game_list[i].richPresenceList[j][0]):
						MCCCampaignDifficulty = 'Heroic'
					elif 'Legendary' in str(game_list[i].richPresenceList[j][0]):
						MCCCampaignDifficulty = 'Legendary'
					if MCCGame == '':
					  if 'H: CE' in str(game_list[i].richPresenceList[j][0]):
						  MCCGame = 'H1'
					  elif 'H: R' in str(game_list[i].richPresenceList[j][0]):
						  MCCGame = 'HR'
					  elif 'H2' in str(game_list[i].richPresenceList[j][0]):
						  MCCGame = 'H2'
					  elif 'H2A' in str(game_list[i].richPresenceList[j][0]):
						  MCCGame = 'H2A'
					  elif 'H3' in str(game_list[i].richPresenceList[j][0]):
						  MCCGame = 'H3'
					  elif 'H4' in str(game_list[i].richPresenceList[j][0]):
						  MCCGame = 'H4'
					  elif 'ODST' in str(game_list[i].richPresenceList[j][0]):
						  MCCGame = 'ODST'
					elif 'Custom' in str(game_list[i].richPresenceList[j][0]):
						MCCMode = 'Custom'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(' - ')+3:]
				elif 'Matchmade Game' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Matchmaking'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(' - ')+3:]
				elif 'Firefight' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Firefight'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(' - ')+3:]
				elif 'Forge' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Forge'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(' - ')+3:]
				elif 'Theater' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Theater'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(' - ')+3:]
				elif 'Spartan Ops' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Spartan Ops'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(' - ')+3:]
				elif 'Main Menu' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Menus'
				else:
					MCCMode = 'Misc.'
				if 'Custom Game' in MCCMap:
				  MCCGame = MCCMap.replace(' Custom Game','')
				  MCCMap = ''
				if 'Firefight' in MCCMap:
				  MCCGame = MCCMap.replace(' Firefight','')
				  MCCMap = ''
				if 'Forge' in MCCMap:
				  MCCGame = MCCMap.replace(' Forge','')
				  MCCMap = ''
				if 'Spartan Ops' in MCCMap:
				  MCCGame = MCCMap.replace(' Spartan Ops','')
				  MCCMap = ''
				if MCCMap == 'Theater':
				  MCCMap = ''
				  
			#Parse H5 rich presence context
			elif 'Halo 5: Guardians' in game_list[i].title:
				if 'Arena' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Arena'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(':')+2:]
				elif 'BTB' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'BTB'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(':')+2:]
				elif 'Firefight' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Firefight'
					MCCMap =  str(game_list[i].richPresenceList[j][0])[str(game_list[i].richPresenceList[j][0]).find(':')+2:]
				elif 'Warzone' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Warzone'
				elif 'Custom' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Customs'
				elif 'Menus' in str(game_list[i].richPresenceList[j][0]) or 'Title Screen' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Menus'
				elif 'Forge' in str(game_list[i].richPresenceList[j][0]) or 'Title Screen' in str(game_list[i].richPresenceList[j][0]):
					MCCMode = 'Forge'
				else:
					MCCMode = 'Campaign'
					MCCMap =  str(game_list[i].richPresenceList[j][0])
			
			#Parse H5 Forge rich presence context
			elif 'Halo 5: Forge' in game_list[i].title:
				MCCMode = str(game_list[i].richPresenceList[j][0])
				
			print("    " + str(game_list[i].richPresenceList[j][0]) + "," + str(game_list[i].richPresenceList[j][1]))
			
			with open(rp_breakdown_current, 'a') as myfile:
				myfile.write(str(game_list[i].title) + "," + str(game_list[i].platform) + "," + str(game_list[i].population) + "," + str(game_list[i].richPresenceList[j][0]) + "," + str(game_list[i].richPresenceList[j][1]) + "," + MCCGame + "," + MCCMode + "," + MCCCampaignDifficulty + "," + MCCMap + "\n")
			with open(rp_breakdown_historical, 'a') as myfile:
				myfile.write(str(game_list[i].title) + "," + str(game_list[i].platform) + "," + str(game_list[i].population) + "," + str(game_list[i].richPresenceList[j][0]) + "," + str(game_list[i].richPresenceList[j][1]) + "," + MCCGame + "," + MCCMode + "," + MCCCampaignDifficulty + "," + MCCMap + "\n")
	  
	  #for games with no rich presence just output their populations
	  else:
		print(str(game_list[i].title) + "," + str(game_list[i].platform) + "," + str(game_list[i].population))
		with open(rp_breakdown_current, 'a') as myfile:
			myfile.write(str(game_list[i].title) + "," + str(game_list[i].platform) + "," + str(game_list[i].population) + "\n")
		with open(rp_breakdown_historical, 'a') as myfile:
			myfile.write(str(game_list[i].title) + "," + str(game_list[i].platform) + "," + str(game_list[i].population) + "\n")

	## Send count to spartanfinder server
	ftp_session = ftplib.FTP(FTP_SERVER,FTP_USER,FTP_PW, timeout=15)
	ftp_file = open(rp_breakdown_current,'rb')
	ftp_session.storbinary('STOR ' + richPresenceOutputFile, ftp_file)     
	ftp_file.close()                                
	ftp_session.quit()
