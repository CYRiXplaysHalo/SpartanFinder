import urllib.request
import time
import json
from datetime import datetime
import socket
import sys
import re

def xlinkScrape(historicalXlinkStatsOutFile, xlinkCurrentH1OutFile, xlinkCurrentH2OutFile, xlinkCurrentH3OutFile,
				xlinkCurrentH3ODSTOutFile, xlinkCurrentH4OutFile, xlinkCurrentReachOutFile, xlinkCurrentMCCOutFile,
				xlinkCurrentTimeStampOutFile):
	req = urllib.request.Request(
            url='http://syndication.twitter.com/timeline/profile?screen_name=popularonxlink',
            data=None, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
            }
        )

	xlink_stats = urllib.request.urlopen(req)
	xlink_stats_json = json.loads(xlink_stats.read().decode('utf-8'))

	latest_tweet = xlink_stats_json['body']
	latest_tweet = latest_tweet[latest_tweet.find('Active in the last hour:'):]
	latest_tweet = cleanhtml(latest_tweet[:latest_tweet.find('\n')])

	tweet_time = xlink_stats_json['body'][xlink_stats_json['body'].find('dt-updated')+22:]
	tweet_time = tweet_time[:19]

	xlink_h2_count = 0
	xlink_h3_count = 0
	xlink_h3_odst_count = 0
	xlink_reach_count = 0
	xlink_h1_count = 0
	xlink_mcc_count = 0
	xlink_h4_count = 0
	if 'Halo 2' in str(latest_tweet):
		h2_num = str(latest_tweet)[str(latest_tweet).find('Halo 2')+17:]
		h2_num = h2_num[:h2_num.find(' ')].strip()
		xlink_h2_count = int(h2_num)
	if 'Halo: Combat Evolved' in str(latest_tweet):
		h1_num = str(latest_tweet)[str(latest_tweet).find('Halo: Combat Evolved')+31:]
		h1_num = h1_num[:h1_num.find(' ')].strip()
		xlink_h1_count = int(h1_num)
	if 'Halo Reach' in str(latest_tweet):
		reach_num = str(latest_tweet)[str(latest_tweet).find('Halo Reach')+24:]
		reach_num = reach_num[:reach_num.find(' ')].strip()
		xlink_reach_count = int(reach_num)
	if 'Halo 3' in str(latest_tweet):
		h3_num = str(latest_tweet)[str(latest_tweet).find('Halo 3')+20:]
		h3_num = h3_num[:h3_num.find(' ')].strip()
		xlink_h3_count = int(h3_num)
	if 'Halo 3 ODST' in str(latest_tweet):
		h3_odst_num = str(latest_tweet)[str(latest_tweet).find('Halo 3 ODST')+25:]
		h3_odst_num = h3_odst_num[:h3_odst_num.find(' ')].strip()
		xlink_h3_odst_count = int(h3_odst_num)
	if 'Halo 4' in str(latest_tweet):
		h4_num = str(latest_tweet)[str(latest_tweet).find('Halo 4')+20:]
		h4_num = h4_num[:h4_num.find(' ')].strip()
		xlink_h4_count = int(h4_num)
	if 'Halo: The Master Chief Collection' in str(latest_tweet):
		mcc_num = str(latest_tweet)[str(latest_tweet).find('Halo: The Master Chief Collection')+47:]
		mcc_num = mcc_num[:mcc_num.find(' ')].strip()
		xlink_mcc_count = int(mcc_num)


	with open(historicalXlinkStatsOutFile, "a") as myfile:
		myfile.write("\"" + datetime + "\",\""+ str(xlink_h1_count) + "\",\"" + str(xlink_h2_count) + "\",\"" + str(xlink_h3_count) + "\",\"" + str(xlink_reach_count) + "\",\"" +  str(xlink_mcc_count) + "\"\n")
	with open(xlinkCurrentH1OutFile, "w") as myfile:
		myfile.write(str(xlink_h1_count))
	with open(xlinkCurrentH2OutFile, "w") as myfile:
		myfile.write(str(xlink_h2_count))
	with open(xlinkCurrentH3OutFile, "w") as myfile:
		myfile.write(str(xlink_h3_count))
	with open(xlinkCurrentH3ODSTOutFile, "w") as myfile:
		myfile.write(str(xlink_h3_odst_count))
	with open(xlinkCurrentH4OutFile, "w") as myfile:
		myfile.write(str(xlink_h4_count))
	with open(xlinkCurrentReachOutFile, "w") as myfile:
		myfile.write(str(xlink_reach_count))
	with open(xlinkCurrentMCCOutFile, "w") as myfile:
		myfile.write(str(xlink_mcc_count))
	with open(xlinkCurrentTimeStampOutFile, "w") as myfile:
		myfile.write(str(tweet_time))
		
	return True
						