# from .preprocess import Preprocess
# from .defines import Functions, Defines
# from .parse import Parse
#
# preprocessor = Preprocess()
# parser = Parse()

import sys
import time
from functools import partial
from httplib import BadStatusLine
from sys import maxint
from urllib2 import URLError
import nltk
from nltk import *
from nltk.probability import FreqDist
import unicodedata

import twitter
import io, json
import pickle
import random
import re

def load_json(filename):
    with io.open(filename,
                 encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    with io.open('{0}.json'.format(filename),
                 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, indent = 1, ensure_ascii=False)))


# def dnc_gop_training_set(gop_tweets, dnc_tweets):
#     gop_dnc_set = []
#     for (words, party) in gop_tweets + dnc_tweets:
#         words_filtered = [e.lower() for e in words.split() if len(e) >= 3]
#         gop_dnc_tweets.append((words_filtered, sentiment))



def clean_tweet(tweet):
    '''
    Utility function to clean the text in a tweet by removing
    links and special characters using regex.
    '''
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

def process(file):
    list = []
    for line in file:
        cl = clean_tweet(line)
        list.append(cl)
    return list
    # save_json(filename+"_tweets", dnc_tweets)
    # save_json(filename+"_likes", dnc_likes)

def extract_tweet_entities(tweets):

    if len(tweets) == 0:
        return [], []

    tweet_texts = [ tweet['text']
                     for tweet in tweets ]
    screen_names = [ user_mention['screen_name']
                         for tweet in tweets
                            for user_mention in tweet['entities']['user_mentions'] ]
    hashtags = [ hashtag['text']
                     for tweet in tweets
                        for hashtag in tweet['entities']['hashtags'] ]

    return tweet_texts, screen_names, hashtags


# def clean(tweet_string):
#     # Cleans irrelevant information from a tweet text`.
#     cleaned_tweet_string = preprocessor.clean(tweet_string, Functions.CLEAN)
#     return cleaned_tweet_string
#
# def tokenize(tweet_string):
#     """Tokenizes irrelevant information in a tweet text`.
#     """
#     tokenized_tweet_string = preprocessor.clean(tweet_string, Functions.TOKENIZE)
#     return tokenized_tweet_string
#
# def parse(tweet_string):
#     """Parses given a tweet text and returns an object`.
#     """
#     parsed_tweet = preprocessor.parse(tweet_string)
#     parsed_tweet_obj = parsed_tweet.urls
#     # parsed_tweet.urls[0].start_index
#     return parsed_tweet_obj
def splitDataset(dataset, splitRatio):
	trainSize = int(len(dataset) * splitRatio)
	trainSet = []
	copy = list(dataset)
	while len(trainSet) < trainSize:
		index = random.randrange(len(copy))
		trainSet.append(copy.pop(index))
	return [trainSet, copy]


def main():
    # dnc_timeline = load_json('dnc_tweets_timeline.json')
    # dnc_likes = load_json('dnc_likes_timeline.json')
    #
    # gop_timeline = load_json('gop_tweets_timeline.json')
    # gop_likes = load_json('gop_likes_timeline.json')
    #
    # dnc_tweet_texts, dnc_tweet_screennames, dnc_tweet_hashtags = extract_tweet_entities(dnc_timeline)
    # dnc_like_texts, dnc_like_screennames, dnc_like_hashtags = extract_tweet_entities(dnc_likes)
    #
    # gop_tweet_texts, gop_tweet_screennames, gop_tweet_hashtags = extract_tweet_entities(gop_timeline)
    # gop_like_texts, gop_like_screennames, gop_like_hashtags = extract_tweet_entities(gop_likes)
    #
    # save_json("dnc_tweet_features", dnc_tweet_texts, dnc_tweet_hashtags)
    # save_json("dnc_like_features", dnc_like_texts, dnc_like_hashtags)
    #
    # save_json("gop_tweet_features", gop_tweet_texts, gop_tweet_hashtags)
    # save_json("gop_like_features", gop_like_texts, gop_like_hashtags)
    #
    # dnc_tweets = load_json('dnc_tweet_features.json')
    # dnc_tweets = process(dnc_tweets)
    # save_json("dnc_tweets_clean", dnc_tweets)
    #
    # dnc_likes = load_json('dnc_like_features.json')
    # dnc_likes = process(dnc_likes)
    # save_json("dnc_likes_clean", dnc_likes)
    #
    # gop_tweets = load_json('gop_tweet_features.json')
    # gop_tweets = process(gop_tweets)
    # save_json("gop_tweets_clean", gop_tweets)
    #
    # gop_likes = load_json('gop_like_features.json')
    # gop_likes = process(gop_likes)
    # save_json("gop_likes_clean", gop_likes)
    splitRatio = 0.67
    dnc_tweets_clean = load_json("dnc_tweets_clean.json")
    dnc_tweets_clean_train, dnc_tweets_clean_test = splitDataset(dnc_tweets_clean, splitRatio)
    save_json("dnc_tweets_clean_train", dnc_tweets_clean_train)

    dnc_likes_clean = load_json("dnc_likes_clean.json")
    dnc_likes_clean_train, dnc_likes_clean_test = splitDataset(dnc_likes_clean, splitRatio)
    save_json("dnc_likes_clean_train", dnc_likes_clean_train)

    gop_tweets_clean = load_json("dnc_tweets_clean.json")
    gop_tweets_clean_train, gop_tweets_clean_test = splitDataset(gop_tweets_clean, splitRatio)
    save_json("gop_tweets_clean_train", gop_tweets_clean_train)

    gop_likes_clean = load_json("gop_likes_clean.json")
    gop_likes_clean_train, gop_likes_clean_test = splitDataset(gop_likes_clean, splitRatio)
    save_json("gop_likes_clean_train", gop_likes_clean_train)

    dnc_tweets_sentiments = jsonToData("dnc_tweets_clean_train.json", "dnc_likes_clean_train.json","democrat")
    gop_tweets_sentiments = jsonToData("gop_tweets_clean_train.json", "gop_likes_clean_train.json","republican")
    # print dnc_tweets_sentiments
    # gop_tweets  = [(tweet, sentiment) for (tweet, sentiment) in gop_tweets_sentiments[:500]]
    all_tweets_sentiments = words_filter_and_sentiment(dnc_tweets_sentiments, gop_tweets_sentiments)

    training_set =  [(extract_features(d, all_tweets_sentiments), c) for (d,c) in all_tweets_sentiments]
    # test_set =  [(extract_features(d, tester), c) for (d,c) in tester]
    save_json("my_training_set", training_set)

    classifier = nltk.NaiveBayesClassifier.train(training_set)

    for t in tester:
        print "{0} : {1}".format(t, classifier.classify(extract_test_features(t.split(), tester)))


if __name__ == "__main__":
    main()


    # # print("got here")
    # dataset = [(extract_features(d, all_tweets_sentiments), c) for (d,c) in all_tweets_sentiments]
    # save_json("dataset", dataset)
    #
    # dataset = load_json("dataset.json")
    # splitRatio = 0.67
    # training_set, test = splitDataset(dataset, splitRatio)
    # print test
    # save_json("training_set", training_set)
    # save_json("test_set", test)
    # print('Split {0} rows into train with {1} and test with {2}').format(len(dataset), training_set, test)
