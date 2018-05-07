import sys
import unicodedata
from nltk.probability import FreqDist
import twitter
import io, json
import random
import re


''' load and save json object '''
def load_json(filename):
    with io.open(filename,
                 encoding='utf-8') as f:
        return json.load(f)

def save_json(filename, data):
    with io.open('{0}.json'.format(filename),
                 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps(data, indent = 1, ensure_ascii=False)))

def clean_tweet(tweet):
    '''
    function to clean the text in a tweet by removing
    links and special characters using regex.
    '''
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())


def process(file):
    '''
    function that calls clean_tweet function to iteratively clean tweets in
    file and returna list of cleaned tweets
    '''
    list = []
    for line in file:
        cl = clean_tweet(line)
        list.append(cl)
    return list

def extract_tweet_entities(tweets):
    '''
    function to extract tweet text and other entities that might be needed
    calls process funtion to return clean tweets
    '''
    if len(tweets) == 0:
        return [], [], []

    tweet_texts = [ tweet['text']
                     for tweet in tweets ]
    screen_names = [ user_mention['screen_name']
                         for tweet in tweets
                            for user_mention in tweet['entities']['user_mentions'] ]
    hashtags = [ hashtag['text']
                     for tweet in tweets
                        for hashtag in tweet['entities']['hashtags'] ]

    tweet_texts = process(tweet_texts)
    # screen_name = process(screen_name)
    # hashtags = process(hashtags)
    return tweet_texts

def jsonToData(filename1, filename2, party):
    '''
    combines two files and appends the classification of the tweets to each text
    returns a dictionary of {tweet['text']: party}
    '''
    tweet_party_dict = []
    texts_json = load_json(filename1)
    likes_json = load_json(filename2)
    for i in texts_json:
        tup = (i, party)
        tweet_party_dict.append(tup)
    for a in likes_json:
        tup = (a, party)
        tweet_party_dict.append(tup)
    return tweet_party_dict


def words_filter_and_classify(tw_sent_1, tw_sent_2):
    '''
    filters out words that are smaller than 2 characters
    and lowercase all the words '''
    tweets = []
    ("words filter")
    for (words, sentiment) in tw_sent_1 + tw_sent_2:
        words_filtered = [e.lower() for e in words.split() if len(e) >= 3]
        tweets.append((words_filtered, sentiment))
    return tweets

def get_word_features(wordlist):
    '''returns the common words in a list of words'''
    wordlist = FreqDist(wordlist)
    word_features = [w for (w, c) in wordlist.most_common(2000)]
    return word_features

def get_words_in_tweets(tweets):
    '''
    returns a list of all the words in
    the dictionary of tweets and sentiment
    '''
    all_words = []
    for (words, sentiment) in tweets:
        all_words += words
    return all_words


def splitDataset(dataset, splitRatio):
    '''
    splits a dataset given a threshold
    returns a training set and a test set
    '''
    trainSize = int(len(dataset) * splitRatio)
    trainSet = []
    copy = list(dataset)
    while len(trainSet) < trainSize:
		index = random.randrange(len(copy))
		trainSet.append(copy.pop(index))
    return [trainSet, copy]

def extract_features(document, tweets):
    '''
    checks the occurrence of words in a tweet
    against an entire document of tweets
    '''
    document_words = set(document)
    features = {}
    word_features = get_word_features(get_words_in_tweets(tweets))
    for word in word_features:
        features['contains(%s)' % word] = (word in document_words)
    return features



def main():

    dnc_timeline = load_json('dnc_tweets_timeline.json')
    dnc_likes = load_json('dnc_likes_timeline.json')

    gop_timeline = load_json('gop_tweets_timeline.json')
    gop_likes = load_json('gop_likes_timeline.json')

    dnc_tweets_clean = extract_tweet_entities(dnc_timeline)
    dnc_likes_clean = extract_tweet_entities(dnc_likes)

    gop_tweets_clean = extract_tweet_entities(gop_timeline)
    gop_likes_clean = extract_tweet_entities(gop_likes)

    splitRatio = 0.67
    dnc_tweets_clean_train, dnc_tweets_clean_test = splitDataset(dnc_tweets_clean, splitRatio)
    save_json("dnc_tweets_clean_train", dnc_tweets_clean_train)

    dnc_likes_clean_train, dnc_likes_clean_test = splitDataset(dnc_likes_clean, splitRatio)
    save_json("dnc_likes_clean_train", dnc_likes_clean_train)

    gop_tweets_clean_train, gop_tweets_clean_test = splitDataset(gop_tweets_clean, splitRatio)
    save_json("gop_tweets_clean_train", gop_tweets_clean_train)

    gop_likes_clean_train, gop_likes_clean_test = splitDataset(gop_likes_clean, splitRatio)
    save_json("gop_likes_clean_train", gop_likes_clean_train)

    dnc_tweets_classify = jsonToData("dnc_tweets_clean_train.json", "dnc_likes_clean_train.json","democrat")
    gop_tweets_classify = jsonToData("gop_tweets_clean_train.json", "gop_likes_clean_train.json","republican")

    all_tweets_sentiments = words_filter_and_classify(dnc_tweets_classify, gop_tweets_classify)

''' training set'''
    training_set =  [(extract_features(d, all_tweets_sentiments), c) for (d,c) in all_tweets_sentiments]
    save_json("my_training_set", training_set)
''' test set'''
    test_set = dnc_tweets_clean_test + dnc_likes_clean + gop_tweets_clean_test + gop_likes_clean_test
    save_json("test_set", test_set)

if __name__ == "__main__":
    main()
