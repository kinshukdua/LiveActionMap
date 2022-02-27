
import ast
import json
import spacy
# from geograpy import places
from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster
NER = spacy.load("en_core_web_sm")
from tqdm import tqdm
import os
from pathlib import Path
from functools import lru_cache
from time import sleep

class Map:
    def __init__(self,tweets_file, dist_dir):
        self.tweets_file = tweets_file
        self.geolocator = Nominatim(user_agent="map ukraine")
        self.m = folium.Map(location = (48.3794, 31.1656), zoom_start=6)
        self.dist_file = os.path.join(dist_dir, 'index.html')
        Path(dist_dir).mkdir(parents=True, exist_ok=True)

    def get_places(self):
        places = []
        with open(self.tweets_file,"r") as f:
            raw_text = f.readlines()
            for tweet_data in raw_text:
                if "'id':" not in tweet_data:
                    continue

                tweet_data = ast.literal_eval(tweet_data)
                tweet = tweet_data['text'].strip()

                if tweet:
                    text= NER(tweet)
                    for word in text.ents:
                        if word.label_ == "GPE" or  word.label_ == "LOC":
                            # print(word.text,word.label_,end=", ")
                            places.append({
                                "place": word.text,
                                "link": tweet_data['link'],
                                "tweet": tweet
                            })
        return places

    def _get_cities_and_regions(words):
        from geograpy import places
        pc = places.PlaceContext(words)
        pc.set_countries()
        pc.set_regions()
        pc.set_cities()
        return pc.cities+pc.regions

    @lru_cache(maxsize=None)
    def _get_geolocation(self, query):
        return self.geolocator.geocode(query)

    @lru_cache(maxsize=None)
    def _get_reverse_geolocation(self, lat, lon):
        return self.geolocator.reverse([lat, lon]).raw

    def generate_map(self, use_filter=True):
        marker_cluster = MarkerCluster().add_to(self.m)
        places = self.get_places()
        if not use_filter:
            # TODO `places` is an array of json, but the following function expects an array of strings
            places = self._get_cities_and_regions(places)
        print("Adding markers... (This may take a while)")
        with tqdm(sorted(places, key=lambda k: k['place'])) as t:
            retry = []
            for tweet_place in t:
                link = tweet_place['link']
                tweet = tweet_place['tweet']
                place = tweet_place['place']
                if place.lower() == "Ukraine".lower():
                    continue
                t.set_description(f"{place}")
                try:
                    geodata = self._get_geolocation(place)
                except:
                    print("Failed to geolocate", place)
                    retry.append(tweet_place)
                    continue
                if geodata is not None:
                    geodata = geodata.raw
                    location = (geodata["lat"], geodata["lon"])
                    rev = self._get_reverse_geolocation(geodata["lat"], geodata["lon"])
                    popup = f"{tweet}<br><a href={link} target=\"_blank\">Tweet</a>"

                    if use_filter:
                        if rev['address']['country_code'] == 'ua':
                            folium.Marker(location=location,icon=folium.Icon(color="red", icon="exclamation-sign"), popup=popup).add_to(marker_cluster)
                    else:
                        folium.Marker(location=location,icon=folium.Icon(color="red", icon="exclamation-sign"), popup=popup).add_to(marker_cluster)

            if retry:
                sleep(10)
                print("Retrying failed geolocations...")
                with tqdm(sorted(retry, key=lambda k: k['place'])) as r:
                    for tweet_place in r:
                        link = tweet_place['link']
                        tweet = tweet_place['tweet']
                        place = tweet_place['place']
                        t.set_description(f"{place}")
                        try:
                            geodata = self._get_geolocation(place)
                        except:
                            continue
                        if geodata is not None:
                            geodata = geodata.raw
                            location = (geodata["lat"], geodata["lon"])
                            rev = self._get_reverse_geolocation(geodata["lat"], geodata["lon"])
                            popup = f"{tweet}<br><a href={link} target=\"_blank\">Tweet</a>"

                            if use_filter:
                                if rev['address']['country_code'] == 'ua':
                                    folium.Marker(location=location,icon=folium.Icon(color="red", icon="exclamation-sign"), popup=popup).add_to(marker_cluster)
                            else:
                                folium.Marker(location=location,icon=folium.Icon(color="red", icon="exclamation-sign"), popup=popup).add_to(marker_cluster)

    def add_borders(self):
        import json
        import requests

        url = (
            "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data"
        )
        style1 = {'fillColor': '#FF00003F', 'color': '#ff0000'}
        country_borders = f"{url}/world-countries.json"
        geo_json_data = json.loads(requests.get(country_borders).text)
        # Add ukraine borders
        folium.GeoJson(geo_json_data['features'][165],style_function=lambda x:style1).add_to(self.m)

    def save_map(self):
        self.m.save(self.dist_file)

    def inject_overlay(self, dist_dir, overlay_dir):
        from bs4 import BeautifulSoup
        from re import compile

        map_file = BeautifulSoup(
            open(self.dist_file, "r").read(),
            "html.parser"
        )
        css_file = open(
            os.path.join(overlay_dir, "overlay.css")
        ).read()

        overlay = BeautifulSoup(
            open(
                os.path.join(overlay_dir, "overlay.html"),
                "r"
            ).read(),
            "html.parser"
        )

        map_div = map_file.find("div", id=compile("map_"))
        map_div["style"] = "z-index: 0;"
        map_div.insert_after(overlay)

        map_file.find("head").append(
            BeautifulSoup("<link rel='stylesheet' href='overlay.css'>",
            "html.parser")
        )

        with open(self.dist_file, "w", encoding="utf-8") as dist_html:
            dist_html.write(str(map_file))

        with open(
                os.path.join(dist_dir, "overlay.css"), "w") as dist_css:
            dist_css.write(css_file)

    def __del__(self):
        del self.m
        del self.geolocator


if __name__ == "__main__":
    tweets_file = "temp/tweets.txt"
    dist_dir = "dist"
    overlay_dir = "overlay-components"

    uk = Map(tweets_file, dist_dir)
    uk.generate_map()
    uk.add_borders()
    uk.save_map()
    uk.inject_overlay(dist_dir, overlay_dir)
