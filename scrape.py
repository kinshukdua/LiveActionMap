"""Scraper class"""
import json

import datetime
import os
from pathlib import Path
import time
import schedule
from dotenv import load_dotenv
import tweepy
from plot import Map

# Load envs from the .env
load_dotenv()


class Scraper:
    """Scraper class will handle twitter data scraping"""

    def __init__(self, bearer_token, temp_dir, dist_dir):
        self.token = bearer_token
        self.client = tweepy.Client(bearer_token)
        self.query = ""
        self.tweets_file = os.path.join(temp_dir, 'tweets.txt')
        self.dist_dir = dist_dir
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        # loading env variable and converting element to int
        self.blacklist_usernames = [int(el)
                                    for el in json.loads(os.getenv('BLACKLIST_USERID',
                                                                   '[]'))
                                    ]

    def _get_user_id(self, username):
        user = self.client.get_user(username=username)
        return user.data.id

    def _write_tweets(self, tweets, verbose=False):
        if verbose:
            print(tweets.includes.get('users'))
        for tweet in tweets.data:
            tweet_data = {
                "author_id": tweet.author_id,
                "id": tweet.id,
                "text": str(tweet.text.encode('utf-8').decode('ascii', 'ignore')),
                "link": f"https://twitter.com/u/status/{tweet.id}"
            }
            user_id = tweet.author_id
            # skip all the tweets from accounts blacklisted
            if user_id in self.blacklist_usernames:
                print(f"Skipping {user_id} because it was found as blacklisted in this environment")
                continue
            if verbose:
                print(tweet_data)
            with open(self.tweets_file, "a", encoding="utf-8") as output_file:
                output_file.write(str(tweet_data))
                output_file.write("\n")

    def update_query(self, hashtags_list, keywords, preposition, add_args="-is:retweet"):
        """Updating query"""
        print("Query updated!")
        str1 = f"({' OR '.join(hashtags_list)})"
        str2 = f"({' OR '.join(keywords)})"
        str3 = f"({' OR '.join(preposition)})"
        str4 = add_args
        self.query = " ".join([str1, str2, str3, str4])

    def scrap_query(self, time_limit=10, verbose=False, **kwargs):
        """Scraping query from recent tweets"""
        if not self.query:
            print("Please update query first!")
            return
        now = datetime.datetime.now(datetime.timezone.utc)
        start = now - datetime.timedelta(minutes=time_limit)
        start = start.isoformat(timespec="seconds")
        kwargs.update({"user.fields": "created_at,description,entities,id,"
                                      "location,name,pinned_tweet_id,profile_image_url,"
                                      "protected,public_metrics,url,username,verified,withheld"})
        tweets = self.client.search_recent_tweets(self.query,
                                                  start_time=start,
                                                  expansions='author_id',
                                                  **kwargs)
        self._write_tweets(tweets, verbose)
        print("Done scraping query.")

    def scrape_users(self, usernames, time_limit=10, verbose=False, **kwargs):
        """Scraping users"""
        now = datetime.datetime.now(datetime.timezone.utc)
        start = now - datetime.timedelta(minutes=time_limit)
        start = start.isoformat(timespec="seconds")
        for user in usernames:
            user_id = self._get_user_id(user)
            # Checking user_id not present in blacklist to optimize performance and api calls
            if user_id in self.blacklist_usernames:
                print(f"Skipping {user_id} because it was found as blacklisted in this environment")
                continue
            tweets = self.client.get_users_tweets(user_id, start_time=start, **kwargs)
            if tweets.data is None:
                print(f"No tweets for {user} in the given time limit!")
                continue
            self._write_tweets(tweets, verbose)
            print("Done scraping users.")

    def plot_map(self):
        """Plotting map"""
        print("Creating Map...")
        ukraine_map = Map(self.tweets_file, self.dist_dir)
        ukraine_map.generate_map()
        ukraine_map.add_borders()
        ukraine_map.save_map()
        # ukraine_map.inject_overlay(self.dist_dir, "overlay-components")
        print("Plotted!")
        del ukraine_map


def scrape(scraper_instance):
    """Handling main function"""
    hashtags = ["#ukraine", "#russianarmy", "#OSINT"]
    prepositions = ['near', '"south of"', '"north of"', '"east of"', '"west of"']
    key_words = ['spotted', 'movement', 'soldiers', 'attacks',
                 'army', 'military', 'vehicles', 'aircraft', 'plane',
                 'shoot', 'shell', 'fight', 'invaders', 'strike', 'tank']

    scraper_instance.update_query(hashtags, key_words, prepositions)
    scraper_instance.scrap_query(time_limit=100)
    scraper_instance.scrape_users(["COUPSURE", "OsintUpdates"], 200)
    scraper_instance.plot_map()


def clear_tweets(temp_dir):
    """Clears the tweets file every 20 or TWEET_DELETION_INTERVAL minutes"""
    tweets_file = os.path.join(temp_dir, 'tweets.txt')
    if os.path.exists(tweets_file):
        os.remove(tweets_file)


if __name__ == "__main__":
    scraper = Scraper(os.environ["BEARER"], "temp", "dist")

    scrape_interval = int(os.getenv('SCRAPE_INTERVAL_MINS') or 10)
    deletion_interval = int(os.getenv('TWEET_DELETION_INTERVAL') or 20)

    schedule.every(scrape_interval).minutes.do(lambda: scrape(scraper))
    schedule.every(deletion_interval).minutes.do(lambda: clear_tweets("temp"))

    print(f"Scheduled scraping for every {scrape_interval} minutes")
    print(f"Scheduled tweet deletion for every {deletion_interval} minutes")

    scrape(scraper)

    while True:
        schedule.run_pending()
        time.sleep(1)
