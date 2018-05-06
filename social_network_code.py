import sys
import time
from functools import partial
from httplib import BadStatusLine
from sys import maxint
from urllib2 import URLError

import twitter
import networkx as nx
import matplotlib.pyplot as plt

# from the twitter cookbook


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


# twitter cookbook


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


# twitter cookbook


def oauth_login():
    # XXX: Go to http://twitter.com/apps/new to create an app and get values
    # for these credentials that you'll need to provide in place of these
    # empty string values that are defined as placeholders.
    # See https://dev.twitter.com/docs/auth/oauth for more information
    # on Twitter's OAuth implementation.

    CONSUMER_KEY = 'e16z7NGljaikIT6UXsqpECoVf'
    CONSUMER_SECRET = 'Qfzr1akSy5LrpRJspb8AjnKszmPdCVCwP9URqtnxSH1ItrlUvz'
    OAUTH_TOKEN = '820130448839938048-OPMdrW5Z7kDnxCJ6UjJVd8JnKGhiRR9'
    OAUTH_TOKEN_SECRET = 'cn22MZPcNQThNWPUhoVLCWq3NKqhoJ4AvWR9BcwozUW86'
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET)

    twitter_api = twitter.Twitter(auth=auth)
    return twitter_api


# Given a user-id return the top five reciprocal friends


def get_my_top_five(twitter_api, id):
    friends_ids, followers_ids = get_friends_followers_ids(twitter_api,
                                                           user_id=id,
                                                           friends_limit=5000,
                                                           followers_limit=5000)

    # get reciprocal friends and use the returned list of reciprocal friends to get each's user profile
    reciprocal_friends = get_reciprocal_friends(friends_ids, followers_ids);
    recip_friends_user_profiles = get_user_profile(twitter_api, user_ids=reciprocal_friends)

    # make a dictionary for the top five user ids and their follower counts
    top_five = {}
    top_five = find_top_five(top_five, recip_friends_user_profiles)
    return top_five.keys()


# edited the crawler function from twitter cookbook


def crawl_recip_friends(twitter_api, screen_name, limit, depth):

    social_network = nx.Graph()

    # Resolve the ID for screen_name and start working with IDs for consistency
    # in storage
    seed_id = str(twitter_api.users.show(screen_name=screen_name)['id'])

    next_queue = get_my_top_five(twitter_api, seed_id)
    # print next_queue
    edge_pairs = [(seed_id, x) for x in next_queue]
    social_network.add_edges_from(edge_pairs)

    d = 1
    while d < depth:
        d += 1
        (queue, next_queue) = (next_queue, [])

        for fid in queue:
            try:
                ids = get_my_top_five(twitter_api, fid)
                # print ids

                edge_pairs = [(fid, x) for x in ids]
                social_network.add_edges_from(edge_pairs)
                next_queue += ids
            except:
                pass

        if social_network.number_of_nodes() >= 100:
            break

    return social_network


def get_reciprocal_friends(friends, followers):
    # case lists of friends and followers into sets and get the intersection
    # to find the list of reciprocal friends
    friends_set = set(friends)
    followers_set = set(followers)
    return list(friends_set.intersection(followers_set))


def compare_top_five(dict, user, followers):
    should_user_be_in_top_five = False
    user_to_be_removed = user;
    # if followers of a new user are greater than the followers of a user already in the top five
    # then return a true boolean and the id of the user that needs to be removed from the top five
    if followers > min(dict.values()):
        should_user_be_in_top_five = True
        user_to_be_removed = [[k for k,v in dict.items() if v == min(dict.values())]]

    return should_user_be_in_top_five, user_to_be_removed


def find_top_five(top_five_dict, user_dict):
    # compares the follower counts of user ids to return a dict of top five user ids with most
    # followers
    for u_profile in user_dict.keys():
        follower_count = user_dict[u_profile]['followers_count']
        # finding the top five
        if len(top_five_dict) < 5:
            top_five_dict[u_profile] = follower_count
        else:
            u_in_top_five, u_to_be_removed = compare_top_five(top_five_dict, u_profile, follower_count)
            if u_in_top_five:
                del top_five_dict[u_to_be_removed[0][0]]
                top_five_dict[u_profile] = follower_count

    return top_five_dict


def main():
    twitter_api = oauth_login()
    mygraph = crawl_recip_friends(twitter_api, 'TheRealDonnaLe', limit=5000, depth=5)

    my_diameter = nx.diameter(mygraph)
    average_dis = nx.average_shortest_path_length(mygraph)

    # list of nodes
    print "List of my edges " + str(mygraph.nodes())
    # list of edges (tuples)
    print "List of my nodes " + str(mygraph.edges())

    print "Diameter of social network graph is " + str(my_diameter)
    print "Average Distance of social network graph is " + str(average_dis)

    # draw my graph and save it
    nx.draw(mygraph)
    plt.savefig("mygraph.png")
    plt.show()


if __name__ == "__main__":
    main()
