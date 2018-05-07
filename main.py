import sys
import time
from functools import partial
from httplib import BadStatusLine
from sys import maxint
from urllib2 import URLError
import nltk
from nltk import *
from nltk.probability import FreqDist
from collections import Counter

import twitter
import io, json
import networkx as nx
import matplotlib.pyplot as plt

def load_json(filename):
    with io.open(filename,
                 encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    with io.open('{0}.json'.format(filename),
                 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, indent = 1, ensure_ascii=False)))

# twitter cookbook
# Example 19. Getting all friends or followers for a user


def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None), "Must have screen_name or user_id, but not both"

    # See https://dev.twitter.com/docs/api/1.1/get/friends/ids and
    # https://dev.twitter.com/docs/api/1.1/get/followers/ids for details
    # on API parameters

    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids,
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids,
                                count=5000)

    friends_ids, followers_ids = [], []

    for twitter_api_func, limit, ids, label in [
        [get_friends_ids, friends_limit, friends_ids, "friends"],
        [get_followers_ids, followers_limit, followers_ids, "followers"]
    ]:

        if limit == 0: continue

        cursor = -1
        while cursor != 0:

            # Use make_twitter_request via the partially bound callable...
            if screen_name:
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else:  # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']

            # print >> sys.stderr, 'Fetched {0} total {1} ids for {2}'.format(len(ids),
            #                                                                 label, (user_id or screen_name))

            # XXX: You may want to store data during each iteration to provide an
            # an additional layer of protection from exceptional circumstances

            if len(ids) >= limit or response is None:
                break

    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]


def get_user_profile(twitter_api, screen_names=None, user_ids=None):
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None), "Must have screen_names or user_ids, but not both"

    items_to_info = {}

    items = screen_names or user_ids

    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See https://dev.twitter.com/docs/api/1.1/get/users/lookup for details.

        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup,
                                            screen_name=items_str)
        else:  # user_ids
            response = make_twitter_request(twitter_api.users.lookup,
                                            user_id=items_str)

        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else:  # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info

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

        # print >> sys.stderr, 'Fetched %i tweets' % (len(tweets),)
        page_num += 1

    print >> sys.stderr, 'Done fetching tweets'
    return results[:max_results]


def harvest_user_likes(twitter_api, screen_name=None, user_id=None, max_results=1000):
    tweet_list=twitter_api.favorites.list(screen_name=screen_name, count=500, since_id=1)

    max_pages = 16
    results = []

	#Fetch the last 500 favorites of the specified username
    # tweet_list=twitter_api.favorites.list(u_id, count=500, since_id=1)
    results += tweet_list
    page_num = 1

    if max_results == 200:
        page_num = max_pages

    while page_num < max_pages and len(tweet_list) > 0 and len(results) < max_results:
        sid = min([ tweet['id'] for tweet in tweet_list]) - 1
        # if screen_name:
        #     tweet_list=twitter_api.favorites.list(screen_name=screen_name, count=500, max_id=sid)
        # else:
        tweet_list=twitter_api.favorites.list(user_id=user_id, count=500, max_id=sid)

        results += tweet_list
        page_num += 1

    print >> sys.stderr, 'Length of likes %i ' % (len(results),)
    return results
	#print json.dumps(urls, indent=1)

# ---------USE TO PULL INFORMATION FROM OFFICIAL PARTY TWITTER ACCOUNTS
# ---------TO BE USED IN TRAINING SET. IS NEVER RUN AGAIN

# def get_republican_training_data(twitter_api, filename):
#     gop_tweets = harvest_user_timeline(twitter_api, screen_name="GOP", max_results=30000)
#     gop_likes = harvest_user_likes(twitter_api, screen_name="GOP")
#     save_json(filename+"_tweets_timeline", gop_tweets)
#     save_json(filename+"_likes_timeline", gop_likes)
#
#
# def get_democrat_training_data(twitter_api, filename):
#     dnc_tweets = harvest_user_timeline(twitter_api, screen_name="TheDemocrats", max_results=30000)
#     dnc_likes = harvest_user_likes(twitter_api, screen_name="TheDemocrats")
#     save_json(filename+"_tweets_timeline", dnc_tweets)
#     save_json(filename+"_likes_timeline", dnc_likes)

# ------- CLASSIFER STUFF

def get_word_features(wordlist):
    # print("in features")
    wordlist = FreqDist(wordlist)
    # word_features = wordlist.keys() # careful here
    word_features = [w for (w, c) in wordlist.most_common(2000)] #use most_common() if you want to select the most frequent words
    return word_features

def get_words_in_tweets(tweets):
    all_words = []
    for (words, sentiment) in tweets:
        all_words += words
    return all_words

def extract_features(document, tweets):
    # print("extracting")
    document_words = set(document)
    features = {}
    word_features = get_word_features(get_words_in_tweets(tweets))
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features

def words_filter_and_sentiment(tw_sent_1, tw_sent_2):
    tweets = []
    ("words filter")
    for (words, sentiment) in tw_sent_1 + tw_sent_2:
        words_filtered = [e.lower() for e in words.split() if len(e) >= 3]
        tweets.append((words_filtered, sentiment))
    return tweets

# CREATES CLASSIFER WITH CLEANED AND PROCESSED DATA AND TRAINING SET.
# THE CLASSIFER CAN BE PASSED TO MANY FUNCTIONS
def create_classifier():
    dnc_tweets_sentiments = jsonToData("dnc_tweets_clean_train.json", "dnc_likes_clean_train.json","democrat")
    gop_tweets_sentiments = jsonToData("gop_tweets_clean_train.json", "gop_likes_clean_train.json","republican")
    all_tweets_sentiments = words_filter_and_sentiment(dnc_tweets_sentiments, gop_tweets_sentiments)
    training_set = load_json("my_training_set.json")
    return [nltk.NaiveBayesClassifier.train(training_set), all_tweets_sentiments]

# USES A LIST OF POLITICAL KEYWORDS TO FILTER OUT TWEETS THAT MAY NOT BE POLITICAL. RETURNS LIST OF TWEETS
def get_political_tweets(tweets):
    keywords_list = ["gun", "trump", "donald", "president", "abortion", "choice", "prolife", "congress", "gun control", "planned parenthood",
                        "vote", "election", "tax", "russia", "left", "rightwing", "dreamers", "immigration", "democrat",
                            "republican", "liberal", "security", "conservative", "daca", "obama", "clinton", "economy"]
    poli_tweets = []
    for twt in tweets:
        for wd in keywords_list:
            if wd in twt:
                poli_tweets.append(twt)
                break
    return poli_tweets

# ------ HELPER Functions

# RETURNS LIST OF ONLY THE TWEET TEXT
def getTweetText(fullTweet):
    tweet_dict = []
    for i in fullTweet:
        t_text = i["text"].encode('utf-8')
        tweet_dict.append(t_text)
    return tweet_dict

# TAKES IN 2 JSON FILES, LOADS THEM, AND RETURNS A LIST OF TUPLES WITH
# TWEETS TEXT THAT HAVE BEEN MARKED WITH THE PARTY THAT TWEETED IT
# [(TEXT, "DEMOCRAT"), (TEXT, "REPUBLICAN")
def jsonToData(filename1, filename2, party):
    tweet_party_dict = []
    tweets_json = load_json(filename1)
    # print(len(something))
    likes_json = load_json(filename2)
    # print(len(likes_json))
    for i in tweets_json:
        tup = (i, party)
        tweet_party_dict.append(tup)
    for a in likes_json:
        tup = (a, party)
        tweet_party_dict.append(tup)
    return tweet_party_dict

# TAKES IN API, CLASSIFER, ALL TWEET THAT HAVE BEEN MARKED, AND SCREEN NAME
# TO RETURN A POLITICAL PARTY AND THE LIKELIHOOD THAT THEY ARE IN THAT
# PARTY
def party_of_user(twitter_api, my_classifier, all_tweets_sentiments, screen_name=None):

    tweets = harvest_user_timeline(twitter_api, screen_name, max_results=3300)
    likes = harvest_user_likes(twitter_api, screen_name)
    poli_tweets = get_political_tweets(getTweetText(tweets)) + get_political_tweets(getTweetText(likes))
    print(screen_name)
    class_results = []
    for t in poli_tweets:
        class_results.append(my_classifier.classify(extract_features(t.split(), all_tweets_sentiments)))
    user_party = Counter(class_results).most_common()
    party_percent = float(user_party[0][1]) / len(poli_tweets)
    return [str(user_party[0][0]), str(party_percent)]
    # print(user_party[0][0] + " " + str(party_percent))


# GET FRIENDS OF USER. HAD TO SET LIMITS LOW BECAUSE IT WAS TAKING TO LONG
def get_my_friends(twitter_api, id):
    friends_ids, followers_ids = get_friends_followers_ids(twitter_api,
                                                           user_id=id,
                                                           friends_limit=15,
                                                           followers_limit=2)

    # make a dictionary for the top five user ids and their follower counts
    friend_user_profiles = get_user_profile(twitter_api, user_ids=friends_ids)
    results = []
    for prof in friend_user_profiles.keys():
        results.append(friend_user_profiles[prof]["screen_name"])
        # results.append(prof.value["screen_name"])
    print(results)
    return results

def crawl_recip_friends(twitter_api, screen_name):

    social_network = nx.Graph()

    # Resolve the ID for screen_name and start working with IDs for consistency
    # in storage
    seed_id = str(twitter_api.users.show(screen_name=screen_name)['id'])

    next_queue = get_my_friends(twitter_api, seed_id)
    edge_pairs = [(seed_id, x) for x in next_queue]
    social_network.add_edges_from(edge_pairs)
    return social_network

def main():
    twitter_api = oauth_login()
    my_classifier, all_tweets_sentiments = create_classifier()
    # REPLACE seanhannity WITH USER SCREEN NAME OF YOUR CHOICE
    mygraph = crawl_recip_friends(twitter_api, 'seanhannity')
    print "List of my nodes " + str(mygraph.nodes())

    color_map = []

# GOES THROUGH THE NODES OF THE GRAPH IN ORDER TO APPLY THE PARTY_OF_USER() function
# TO EACH OF THE ACCOUNTS THAT THE USER FOLLOWS.
# IF THE NODE IS A REPUBLICAN, IT WILL BE red
# IF IT IS DEMOCRAT, IT WILL BE blue
# TRYING TO VISUALIZE THE POLITICAL SOCIAL NETWORK OF THE USER
    for nd in mygraph.nodes:
        # HAD TO TAKE OUT THE USER NODE BECAUSE IT IS NOT A SCREEN NAME
        #  AND WAS CAUSING ISSUES
        if nd == '41634520':
            continue
        party, percent = party_of_user(twitter_api, my_classifier, all_tweets_sentiments, screen_name=nd)
        print(party + " " + percent)

        if party == "republican":
            color_map.append('red')
        else:
            color_map.append('blue')

        # draw my graph and save it
    nx.draw(mygraph, node_color = color_map)
    plt.savefig("mygraph.png")
    plt.show()


if __name__ == "__main__":
    main()
