import sys
import time
from functools import partial
from httplib import BadStatusLine
from sys import maxint
from urllib2 import URLError

import twitter
import twitter
import io, json

def save_json(filename, data):
    with io.open('{0}.json'.format(filename),
                 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, indent=1))) 

def oauth_login():
	CONSUMER_KEY = 'QQ8tvYublOKYWNXncsz6yAaTF'
	CONSUMER_SECRET = 'XQ7NdcMUcXYhChh4ec4inMFn0aRRWTjTL6s2L6fLsuKiFWterz'
	OAUTH_TOKEN = '934175051930308609-CNSI6N2RdSHPBbBd2gatkK4887JKCQS'
	OAUTH_TOKEN_SECRET = 'bHgJnEQrIINjBjJQhVKvaYzw8pOVAQEcG936eBYQJx63x'

	auth = twitter.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
							CONSUMER_KEY, CONSUMER_SECRET)

	twitter_api = twitter.Twitter(auth=auth)
	return twitter_api

#likes_result = twitter_api.search.favourites_count

def harvest_user_likes(twitter_api, screen_name=None, user_id=None, max_results=1000):
	
	#define array of urls
	urls={}

	#Fetch the last 500 favorites of the specified username
	tweet_list=twitter_api.favorites.list(screen_name="your_username", count=max_results)

	#loop through the list of tweets
	for tweet in tweet_list:
		try:
			
			#get the expanded_url
			#url=tweet['entities']['urls'][0]['expanded_url']
			
			#this is the short_url
			url=tweet['entities']['urls'][0]['url']
			
			#this is the text of the tweet
			tweet_text=tweet['text']
			
			#add url to array of urls
			#urls.append(url)			
			urls[tweet_text] = url
			
			print 'added url: '+ url + 'to array'
			
		except Exception, e:
			print 'no url in tweet'
			#print e
	print 'Length of Tweet Lsit = ' + str(len(tweet_list))
	return urls
	#print json.dumps(urls, indent=1)
	
def main():
    twitter_api = oauth_login()
    likes = harvest_user_likes(twitter_api, screen_name="reallychizzy", max_results=200)
    save_json("likes", likes)
	

if __name__ == "__main__":
    main()
