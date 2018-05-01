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

def jsonToData(filename1, filename2, party):
    tweet_party_dict = []
    something = load_json(filename1)
    # print(len(something))
    likes_json = load_json(filename2)
    # print(len(likes_json))
    for i in something:
        tup = (i["text"].encode('utf-8'), party)
        tweet_party_dict.append(tup)
    for a in likes_json:
        tup = (a["text"].encode('utf-8'), party)
        tweet_party_dict.append(tup)
    return tweet_party_dict


def oneJSONToData(filename):
    tweet_dict = []
    something = load_json(filename)
    for i in something:
        t_text = i["text"].encode('utf-8')
        tweet_dict.append(t_text)
    return tweet_dict


def words_filter_and_sentiment(tw_sent_1, tw_sent_2):
    tweets = []
    ("words filter")
    for (words, sentiment) in tw_sent_1 + tw_sent_2:
        words_filtered = [e.lower() for e in words.split() if len(e) >= 3]
        tweets.append((words_filtered, sentiment))
    return tweets


def test_words_filter_and_sentiment(tw_sent):
    tweets = []
    ("words filter")
    for (words, sentiment) in tw_sent:
        words_filtered = [e.lower() for e in words.split() if len(e) >= 3]
        tweets.append((words_filtered, sentiment))
    return tweets


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


    # ----tester

def get_test_words_in_tweets(tweets):
    all_words = []
    for words in tweets:
        all_words += words
    return all_words

def extract_test_features(document, tweets):
    # print("extracting")
    document_words = set(document)
    features = {}
    word_features = get_word_features(get_test_words_in_tweets(tweets))
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features

def main():
    dnc_tweets_sentiments = jsonToData("dnc_tweets_timeline.json", "dnc_likes_timeline.json","democrat")
    gop_tweets_sentiments = jsonToData("gop_tweets_timeline.json", "gop_likes_timeline.json","republican")
    all_tweets_sentiments = words_filter_and_sentiment(dnc_tweets_sentiments, gop_tweets_sentiments)
    # print("got here")
    training_set = [(extract_features(d, all_tweets_sentiments), c) for (d,c) in all_tweets_sentiments]
    # save_json("training_set", training_set)

    classifier = nltk.NaiveBayesClassifier.train(training_set)
    test_set = oneJSONToData("likes.json")
    print(test_set)

    for t in test_set:
        print "{0} : {1}".format(t, classifier.classify(extract_test_features(t.split(), test_set)))

    # print(len(dnc_tweets_sentiments))
    # print(dnc_tweets_sentiments)


if __name__ == "__main__":
    main()
