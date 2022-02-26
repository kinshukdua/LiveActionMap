import tweepy
import datetime
from plot import Map
import os
from pathlib import Path
import schedule
import time
from dotenv import load_dotenv

# Load envs from the .env
load_dotenv()

class Scraper:
    def __init__(self, bearer_token, temp_dir, dist_dir):
        self.token = bearer_token
        self.client = tweepy.Client(bearer_token)
        self.query = ""
        self.tweets_file = os.path.join(temp_dir, 'tweets.txt')
        self.dist_dir = dist_dir
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_user_id(self,username):
        user = self.client.get_user(username=username)
        return user.data.id

    def _write_tweets(self, tweets, verbose=False):
        for tweet in tweets.data:
            if verbose:
                print(str(tweet.text.encode('utf-8').decode('ascii','ignore')))
            with open(self.tweets_file,"a") as f:
                f.write(str(tweet.text.encode('utf-8').decode('ascii','ignore')))
                f.write("\n")

    
    def update_query(self, hashtags, keywords, preposition, add_args ="-is:retweet"):
        print("Query updated!")
        str1 = f"({' OR '.join(hashtags)})"
        str2 = f"({' OR '.join(keywords)})"
        str3 = f"({' OR '.join(preposition)})"
        str4 = add_args
        self.query = " ".join([str1,str2,str3,str4])
    
    def scrap_query(self, time_limit=10, verbose=False, **kwargs):
        if not self.query:
            print("Please update query first!")
            return
        now = datetime.datetime.now(datetime.timezone.utc)
        start = now -  datetime.timedelta(minutes=time_limit)
        start = start.isoformat(timespec="seconds")
        tweets = self.client.search_recent_tweets(self.query, start_time=start, **kwargs)
        self._write_tweets(tweets, verbose)
        print("Done scraping query.")

    def scrape_users(self, usernames, time_limit=10, verbose=False, **kwargs):
        now = datetime.datetime.now(datetime.timezone.utc)
        start = now -  datetime.timedelta(minutes=time_limit)
        start = start.isoformat(timespec="seconds")
        for user in usernames:
            user_id =  self._get_user_id(user)
            tweets = self.client.get_users_tweets(user_id, start_time=start, **kwargs)
            if tweets.data is None:
                print(f"No tweets for {user} in the given time limit!")
                continue
            self._write_tweets(tweets, verbose)
            print("Done scraping users.")
    def plot_map(self):
        print("Creating Map...")
        uk = Map(self.tweets_file, self.dist_dir)
        uk.generate_map()
        uk.add_borders()
        uk.save_map()
        print("Plotted!")
        del uk

def scrape(scraper):
    hashtags = ["#ukraine","#russianarmy"]
    prepositions = ['near', '"south of"', '"north of"', '"east of"', '"west of"']
    key_words = ['spotted', 'movement', 'soldiers', 'attacks', 'army', 'military', 'vehicles', 'aircraft', 'plane', 'shoot', 'shell', 'fight', 'invaders', 'strike', 'tank']

    scraper.update_query(hashtags,key_words,prepositions)
    scraper.scrap_query(time_limit=100)
    scraper.scrape_users(["COUPSURE","OsintUpdates"], 200)
    scraper.plot_map()

# EXAMPLE
if __name__ == "__main__":
    bearer_token = os.environ["BEARER"]
    scraper = Scraper(bearer_token, "temp", "dist")
    
    interval = int(os.getenv('SCRAPE_INTERVAL_MINS') or 10)
    schedule.every(interval).minutes.do(lambda: scrape(scraper))
    print(f"Scheduled scraping for every {interval} minutes")
    scrape(scraper)

    while True:
        schedule.run_pending()
        time.sleep(1)
