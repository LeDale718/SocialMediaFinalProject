import json
import twitter
from functools import partial
from sys import maxint


def save_json(filename, data):
    with io.open('{0}.json'.format(filename),
                 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, ensure_ascii=False)))

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


def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None, friends_limit=maxint, followers_limit=maxint):
	
	# Must have either screen_name or user_id (logical xor)
	assert (screen_name != None) != (user_id != None), \
	"Must have screen_name or user_id, but not both"
	# See https://dev.twitter.com/docs/api/1.1/get/friends/ids and
	# https://dev.twitter.com/docs/api/1.1/get/followers/ids for details
	# on API parameters
	
	get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids, count=5000)
	get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids, count=5000)
	
	friends_ids, followers_ids = [], []
	
	for twitter_api_func, limit, ids, label in [[get_friends_ids, friends_limit, friends_ids, "friends"],
					[get_followers_ids, followers_limit, followers_ids, "followers"]]:
	
		if limit == 0: continue
		
		cursor = -1
		while cursor != 0:
		
			# Use make_twitter_request via the partially bound callable...
			if screen_name:
				response = twitter_api_func(screen_name=screen_name, cursor=cursor)
			else: # user_id
				response = twitter_api_func(user_id=user_id, cursor=cursor)
			
			if response is not None:
				ids += response['ids']
				
				cursor = response['next_cursor']
			print >> sys.stderr, 'Fetched {0} total {1} ids for {2}'.format(len(ids), label, (user_id or screen_name))
		# XXX: You may want to store data during each iteration to provide an
		# an additional layer of protection from exceptional circumstances
			
			if len(ids) >= limit or response is None:
				break
	
	# Do something useful with the IDs, like store them to disk...
	return friends_ids[:friends_limit], followers_ids[:followers_limit]
	
	
def main():
    twitter_api = oauth_login()
    friends_ids, followers_ids = get_friends_followers_ids(twitter_api, screen_name="foxxymimi", friends_limit=10, followers_limit=10)
	#print friends_ids
	#print followers_ids													
    save_json("user_followers", tweets)
	

if __name__ == "__main__":
    main()



