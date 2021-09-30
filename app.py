import json
import logging
import os
import time
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
sqs_client = SQSClient('tweet-processor')

MESSAGE_TYPE_SCHEDULE_TWEET = 'SCHEDULE_TWEET'
MESSAGE_TYPE_PROCESS_TWEET = 'PROCESS_TWEET'


class TweetScheduleMessage:
    def __init__(self, message_type, tweet, tweet_time=0):
        self.message_type = message_type
        self.tweet = tweet
        self.tweet_time = tweet_time

    def render(self):
        return json.dumps({
            'message_type': self.message_type,
            'tweet': self.tweet,
            'tweet_time': self.tweet_time
        })


def tweet_session(shift_length, google_sheets_key, worksheet_number):
    logger.info(f'Loading tweets from Google Sheets doc - key=[{google_sheets_key}] worksheet=[{worksheet_number}]')
    rows = gsheets_client.read_from_spreadsheet(google_sheets_key, worksheet_number)
    logger.debug(f'Loaded [{len(rows)}] rows from worksheet')
    start_time = int(time.time())
    for row in rows:
        tweet = row[0].rstrip()
        logger.info(f'Loaded tweet from sheet [{tweet}]')
        if len(tweet) > 280:
            logger.warning(f'Tweet length exceed max of 280 characters [{tweet}]')
            continue
        if not tweet:
            continue
        message = TweetScheduleMessage(
            message_type=MESSAGE_TYPE_SCHEDULE_TWEET,
            tweet=tweet,
            tweet_time=start_time
        )
        sqs_client.send_message(message.render())


@app.schedule(Cron(0, 15, '?', '*', '*', '*'))
def nightly_tweet_session(event):
    tweet_session(14400, google_sheets_key, 0)


@app.on_sqs_message(queue='tweet-processor', batch_size=1)
def tweet_processor(event):
    logger.info(f'Got event [{event}]')
    for record in event:
        logger.info(f'Received message on queue with contents [{record.body}]')
        message = TweetScheduleMessage(**json.loads(record.body))
        send_tweet = False
        if message.message_type == MESSAGE_TYPE_SCHEDULE_TWEET:
            current_time = int(time.time())
            if current_time >= message.tweet_time:
                logger.info(
                    f'Current time [{current_time}] is > tweet time [{message.tweet_time}. Sending tweet now!'
                )
                # send_tweet = True
            else:
                pass
        elif message.message_type == MESSAGE_TYPE_PROCESS_TWEET:
            send_tweet = True
        else:
            logger.warning(f'Got unknown message type [{message.message_type}]')
        if send_tweet:
            logger.info(f'Sending tweet [{message.tweet}')
            #twitter_client.send_tweet(message.tweet)
