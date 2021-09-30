import logging
import os
import tweepy

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', logging.INFO))


class TwitterClientException(Exception):
    pass


class TwitterClient:

    def __init__(self, credentials):
        auth = tweepy.OAuthHandler(credentials['consumer_key'], credentials['consumer_secret'])
        auth.set_access_token(credentials['access_token'], credentials['access_token_secret'])
        self.twitter_api = tweepy.API(auth)

    def send_tweet(self, tweet):
        try:
            self.twitter_api.update_status(tweet)
        except tweepy.error.TweepError as e:
            logger.error(f'Error sending tweet: [{e}]')
            raise TwitterClientException
