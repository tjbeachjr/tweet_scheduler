import json
import logging
import os
import time
import sys
from chalice import Chalice, Cron
from chalicelib.google_sheets_client import GoogleSheetsClient
from chalicelib.secrets_manager import get_secret
from chalicelib.sqs_client import SQSClient
from chalicelib.twitter_client import TwitterClient

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOG_LEVEL', logging.INFO))

app = Chalice(app_name='tweet_scheduler')
secrets = get_secret()
twitter_client = TwitterClient(json.loads(secrets['twitter']))
gsheets_client = GoogleSheetsClient(json.loads(secrets['google']))
google_sheets_key = secrets['google_sheets_key']
sqs_client = SQSClient(os.environ['QUEUE_NAME'])


class TweetScheduleMessage:
    def __init__(self, tweet, tweet_time=0):
        self.tweet = tweet
        self.tweet_time = tweet_time

    def render(self):
        return json.dumps({
            'tweet': self.tweet,
            'tweet_time': self.tweet_time
        })


def tweet_session(shift_length, google_sheets_key, worksheet_number):
    logger.info(f'Loading tweets from Google Sheets doc - key=[{google_sheets_key}] worksheet=[{worksheet_number}]')
    rows = gsheets_client.read_from_spreadsheet(google_sheets_key, worksheet_number)
    logger.debug(f'Loaded [{len(rows)}] rows from worksheet')
    tweets = []
    for row in rows:
        tweet = row[0].rstrip()
        logger.info(f'Loaded tweet from sheet [{tweet}]')
        if len(tweet) > 280:
            logger.warning(f'Tweet length exceed max of 280 characters [{tweet}]')
            continue
        if not tweet:
            logger.warning('Empty tweet found - skipping...')
            continue
        tweets.append(tweet)
    if not tweets:
        logger.error('No tweets to send')
        sys.exit(1)
    tweet_time = int(time.time())
    time_between_tweets = int(shift_length / len(tweets))
    logger.info(f'Scheduling tweet [{len(tweets)}] with [{time_between_tweets}] second delay between')
    for tweet in tweets:
        tweet_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(tweet_time))
        logger.info(f'Scheduling tweet [{tweet}] for [{tweet_time_str}] GMT')
        message = TweetScheduleMessage(
            tweet=tweet,
            tweet_time=tweet_time
        )
        sqs_client.send_message(message.render())
        tweet_time += time_between_tweets
    logger.info('All tweets have been scheduled')


@app.schedule(Cron(0, 0, '?', '*', '*', '*'))
def nightly_tweet_session(event):
    shift_length = int(os.environ['NIGHTLY_SHIFT_LENGTH'])
    logger.info(f'Starting nightly tweet session with shift length [{shift_length}] seconds')
    tweet_session(shift_length, google_sheets_key, 0)


@app.schedule(Cron(0, 14, '?', '*', '*', '*'))
def north_america_tweet_session(event):
    shift_length = int(os.environ['NORTH_AMERICA_SHIFT_LENGTH'])
    logger.info(f'Starting North America tweet session with shift length [{shift_length}] seconds')
    tweet_session(shift_length, google_sheets_key, 1)


@app.on_sqs_message(queue=os.environ['QUEUE_NAME'], batch_size=1)
def tweet_processor(event):
    logger.info(f'Got event [{event}]')
    for record in event:
        logger.info(f'Received message on queue with contents [{record.to_dict()}]')
        message = TweetScheduleMessage(**json.loads(record.body))
        tweet_time = int(message.tweet_time)
        receipt_handle = record.receipt_handle
        current_time = int(time.time())
        if current_time >= tweet_time:
            logger.info(
                f'Current time [{current_time}] is > tweet time [{tweet_time}]. Sending tweet [{message.tweet}] now!'
            )
            # twitter_client.send_tweet(message.tweet)
            sqs_client.delete_message(receipt_handle)
        else:
            timeout = int(tweet_time) - current_time
            logger.info(f'Tweet is not ready for sending.  Setting visibility timeout to [{timeout}] seconds')
            sqs_client.change_visibility_timeout(receipt_handle, timeout)
