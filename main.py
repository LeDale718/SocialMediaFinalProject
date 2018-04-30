import sys
import time
from functools import partial
from httplib import BadStatusLine
from sys import maxint
from urllib2 import URLError

import twitter
import io, json

def save_json(filename, data):
    with io.open('{0}.json'.format(filename),
                 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, indent = 1, ensure_ascii=False)))

def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw):
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):

        if wait_period > 3600:  # Seconds
            print >> sys.stderr, 'Too many retries. Quitting.'
            raise e

        # See https://dev.twitter.com/docs/error-codes-responses for common codes

        if e.e.code == 401:
            print >> sys.stderr, 'Encountered 401 Error (Not Authorized)'
            return None
        elif e.e.code == 404:
            print >> sys.stderr, 'Encountered 404 Error (Not Found)'
            return None
        elif e.e.code == 429:
            print >> sys.stderr, 'Encountered 429 Error (Rate Limit Exceeded)'
            if sleep_when_rate_limited:
                print >> sys.stderr, "Retrying in 15 minutes...ZzZ..."
                sys.stderr.flush()
                time.sleep(60 * 15 + 5)
                print >> sys.stderr, '...ZzZ...Awake now and trying again.'
                return 2
            else:
                raise e  # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print >> sys.stderr, 'Encountered %i Error. Retrying in %i seconds' % (e.e.code, wait_period)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function

    wait_period = 2
    error_count = 0

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError, e:
            error_count = 0
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError, e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print >> sys.stderr, "URLError encountered. Continuing."
            if error_count > max_errors:
                print >> sys.stderr, "Too many consecutive errors...bailing out."
                raise
        except BadStatusLine, e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print >> sys.stderr, "BadStatusLine encountered. Continuing."
            if error_count > max_errors:
                print >> sys.stderr, "Too many consecutive errors...bailing out."
                raise

def oauth_login():
	CONSUMER_KEY = 'QQ8tvYublOKYWNXncsz6yAaTF'
	CONSUMER_SECRET = 'XQ7NdcMUcXYhChh4ec4inMFn0aRRWTjTL6s2L6fLsuKiFWterz'
	OAUTH_TOKEN = '934175051930308609-CNSI6N2RdSHPBbBd2gatkK4887JKCQS'
	OAUTH_TOKEN_SECRET = 'bHgJnEQrIINjBjJQhVKvaYzw8pOVAQEcG936eBYQJx63x'

	auth = twitter.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
							CONSUMER_KEY, CONSUMER_SECRET)

	twitter_api = twitter.Twitter(auth=auth)
	return twitter_api

def harvest_user_timeline(twitter_api, screen_name=None, user_id=None, max_results=1000):

    assert (screen_name != None) != (user_id != None),     "Must have screen_name or user_id, but not both"

    kw = {  # Keyword args for the Twitter API call
        'count': 200,
        'trim_user': 'true',
        'include_rts' : 'true',
        'since_id' : 1
        }

    if screen_name:
        kw['screen_name'] = screen_name
    else:
        kw['user_id'] = user_id

    max_pages = 16
    results = []

    tweets = make_twitter_request(twitter_api.statuses.user_timeline, **kw)

    if tweets is None: # 401 (Not Authorized) - Need to bail out on loop entry
        tweets = []

    results += tweets
    print >> sys.stderr, 'Fetched %i tweets' % len(tweets)

    page_num = 1

    if max_results == kw['count']:
        page_num = max_pages # Prevent loop entry

    while page_num < max_pages and len(tweets) > 0 and len(results) < max_results:

        # Necessary for traversing the timeline in Twitter's v1.1 API:
        # get the next query's max-id parameter to pass in.
        # See https://dev.twitter.com/docs/working-with-timelines.
        kw['max_id'] = min([ tweet['id'] for tweet in tweets]) - 1

        tweets = make_twitter_request(twitter_api.statuses.user_timeline, **kw)
        results += tweets

        print >> sys.stderr, 'Fetched %i tweets' % (len(tweets),)
        page_num += 1

    print >> sys.stderr, 'Done fetching tweets'
    return results[:max_results]


def harvest_user_likes(twitter_api, screen_name=None, user_id=None, max_results=1000):

    max_pages = 16
    results = []

	#Fetch the last 500 favorites of the specified username
    tweet_list=twitter_api.favorites.list(screen_name=screen_name, count=500, since_id=1)
    results += tweet_list
    page_num = 1

    if max_results == 200:
        page_num = max_pages

    while page_num < max_pages and len(tweet_list) > 0 and len(results) < max_results:
        sid = min([ tweet['id'] for tweet in tweet_list]) - 1
        tweet_list=twitter_api.favorites.list(screen_name=screen_name, count=500, max_id=sid)
        results += tweet_list
        page_num += 1
	# #loop through the list of tweetss
	# for tweet in results:
	# 	try:
    #
	# 		#get the expanded_url
	# 		#url=tweet['entities']['urls'][0]['expanded_url']
	# 		#this is the text of the tweet
	# 		tweet_text=tweet['text']
	# 		print str(tweet_text)
    #
	# 	except Exception, e:
	# 		print 'no url in tweet'
	# 		#print e
    print >> sys.stderr, 'Length of likes %i ' % (len(results),)
    return results
	#print json.dumps(urls, indent=1)

def get_republican_training_data(twitter_api, filename):
    gop_tweets = harvest_user_timeline(twitter_api, screen_name="GOP", max_results=30000)
    gop_likes = harvest_user_likes(twitter_api, screen_name="GOP")
    save_json(filename+"_tweets_timeline", gop_tweets)
    save_json(filename+"_likes_timeline", gop_likes)


def get_democrat_training_data(twitter_api, filename):
    dnc_tweets = harvest_user_timeline(twitter_api, screen_name="TheDemocrats", max_results=30000)
    dnc_likes = harvest_user_likes(twitter_api, screen_name="TheDemocrats")
    save_json(filename+"_tweets_timeline", dnc_tweets)
    save_json(filename+"_likes_timeline", dnc_likes)


def main():
    twitter_api = oauth_login()
    # tweets = harvest_user_timeline(twitter_api, screen_name="foxxymimi", max_results=200)
    # save_json("retweets_timeline", tweets)

    # likes = harvest_user_likes(twitter_api, screen_name="reallychizzy")
    # print(likes)
    # save_json("likes", likes)


    # ----- Dont run this code again unless you change the filename, it will
    # ----- overwrite the json data files
    # get_republican_training_data(twitter_api,"gop")
    # get_democrat_training_data(twitter_api,"dnc")


if __name__ == "__main__":
    main()
