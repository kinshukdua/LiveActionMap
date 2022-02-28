"""Plotting module"""
# pylint: disable=C0415
import os
from pathlib import Path
from functools import lru_cache
from time import sleep
import ast
from tqdm import tqdm
import folium
import spacy
from folium.plugins import MarkerCluster
# from geograpy import places
from geopy.geocoders import Nominatim

NER = spacy.load("en_core_web_sm")


class Map:
    """Map that handles plotting"""

    def __init__(self, tweets_file_param, dist_dir_param):
        self.tweets_file = tweets_file_param
        self.geolocator = Nominatim(user_agent="LiveActionMap")
        self.map = folium.Map(location=(48.3794, 31.1656), zoom_start=6)
        self.dist_file = os.path.join(dist_dir_param, 'index.html')
        self.dist_dir = dist_dir_param
        Path(self.dist_dir).mkdir(parents=True, exist_ok=True)

    def get_places(self):
        """Get places method"""
        places = []
        with open(self.tweets_file, "r", encoding="utf-8") as input_file:
            raw_text = input_file.readlines()
            for tweet_data in raw_text:
                if "'id':" not in tweet_data:
                    continue

                tweet_data = ast.literal_eval(tweet_data)
                tweet = tweet_data['text'].strip()

                if tweet:
                    text = NER(tweet)
                    for word in text.ents:
                        if word.label_ in ('GPE', 'LOC'):
                            # print(word.text,word.label_,end=", ")
                            places.append({
                                "place": word.text,
                                "link": tweet_data['link'],
                                "tweet": tweet
                            })
        return places

    @staticmethod
    def _get_cities_and_regions(words):
        from geograpy import places
        places = places.PlaceContext(words)
        places.set_countries()
        places.set_regions()
        places.set_cities()
        return places.cities + places.regions

    @lru_cache(maxsize=None)
    def _get_geolocation(self, query):
        return self.geolocator.geocode(query)

    @lru_cache(maxsize=None)
    def _get_reverse_geolocation(self, lat, lon):
        return self.geolocator.reverse([lat, lon]).raw

    def generate_map(self, use_filter=True):
        # pylint: disable=R0914, R0912, R0915
        """Generating map"""
        marker_cluster = MarkerCluster().add_to(self.map)
        places = self.get_places()
        if not use_filter:
            # TODO `places` is an array of json,
            # but the following function expects an array of strings
            places = self._get_cities_and_regions(places)
        print("Adding markers... (This may take a while)")
        with tqdm(sorted(places, key=lambda k: k['place'])) as t_variable:
            retry = []
            for tweet_place in t_variable:
                link = tweet_place['link']
                tweet = tweet_place['tweet']
                place = tweet_place['place']
                place = place.replace("#", "")
                if place.lower() == "Ukraine".lower():
                    continue
                t_variable.set_description(f"{place}")
                # pylint: disable = W0702
                try:
                    geodata = self._get_geolocation(place)
                except:
                    print("Failed to geolocate", place)
                    retry.append(tweet_place)
                    continue
                if geodata is not None:
                    geodata = geodata.raw
                    location = (geodata["lat"], geodata["lon"])
                    rev = self._get_reverse_geolocation(
                        geodata["lat"], geodata["lon"])
                    summary = tweet[0:100] + "..."
                    popup = f"{summary}<br><a href={link} target=\"_blank\">Tweet</a>"

                    if use_filter:
                        if rev['address']['country_code'] == 'ua':
                            folium.Marker(location=location,
                                          icon=folium.Icon(color="red", icon="exclamation-sign"),
                                          popup=popup).add_to(marker_cluster)
                    else:
                        folium.Marker(location=location,
                                      icon=folium.Icon(color="red", icon="exclamation-sign"),
                                      popup=popup).add_to(marker_cluster)

            if retry:
                sleep(10)
                print("Retrying failed geolocations...")
                with tqdm(sorted(retry, key=lambda k: k['place'])) as r_variable:
                    for tweet_place in r_variable:
                        link = tweet_place['link']
                        tweet = tweet_place['tweet']
                        place = tweet_place['place']
                        place = place.replace("#", "")
                        if place.lower() == "Ukraine".lower():
                            continue
                        t_variable.set_description(f"{place}")
                        # pylint: disable = W0702
                        try:
                            geodata = self._get_geolocation(place)
                        except:
                            continue
                        if geodata is not None:
                            geodata = geodata.raw
                            location = (geodata["lat"], geodata["lon"])
                            rev = self._get_reverse_geolocation(
                                geodata["lat"], geodata["lon"])
                            popup = f"{tweet}<br><a href={link} target=\"_blank\">Tweet</a>"

                            if use_filter:
                                if rev['address']['country_code'] == 'ua':
                                    folium.Marker(location=location,
                                                  icon=folium.Icon(color="red",
                                                                   icon="exclamation-sign"),
                                                  popup=popup).add_to(marker_cluster)
                            else:
                                folium.Marker(location=location,
                                              icon=folium.Icon(color="red",
                                                               icon="exclamation-sign"),
                                              popup=popup).add_to(marker_cluster)

    def add_borders(self):
        """Add borders"""
        import json
        import requests

        url = (
            "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data"
        )
        style1 = {'fillColor': '#FF00003F', 'color': '#ff0000'}
        country_borders = f"{url}/world-countries.json"
        geo_json_data = json.loads(requests.get(country_borders).text)
        # Add ukraine borders
        folium.GeoJson(geo_json_data['features'][165],
                       style_function=lambda x: style1).add_to(self.map)

    def save_map(self):
        """Saving map persistent memory"""
        from shutil import copy
        copy(os.path.join("template", "main.css"), self.dist_dir)
        copy(os.path.join("template", "index.html"), self.dist_dir)
        copy(os.path.join("template", "favicon.png"), self.dist_dir)
        copy(os.path.join("images", "map.png"), self.dist_dir)
        self.map.save(self.dist_file)

    def inject_overlay(self, dist_dir, overlay_dir):
        # pylint: disable = R1732
        """Inject overlay"""
        from bs4 import BeautifulSoup
        from re import compile as re_compile

        map_file = BeautifulSoup(
            open(self.dist_file, "r",
                 encoding="utf-8").read(),
            "html.parser"
        )
        css_file = open(
            os.path.join(overlay_dir, "overlay.css"),
            encoding="utf-8"
        ).read()

        overlay = BeautifulSoup(
            open(
                os.path.join(overlay_dir, "overlay.html"),
                "r",
                encoding="utf-8"
            ).read(),
            "html.parser"
        )

        map_div = map_file.find("div", id=re_compile("map_"))
        map_div["style"] = "z-index: 0;"
        map_div.insert_after(overlay)

        map_file.find("head").append(
            BeautifulSoup("<link rel='stylesheet' href='overlay.css'>",
                          "html.parser")
        )

        with open(self.dist_file, "w", encoding="utf-8") as dist_html:
            dist_html.write(str(map_file))

        with open(
                os.path.join(dist_dir, "overlay.css"), "w",
                encoding="utf-8") as dist_css:
            dist_css.write(css_file)

    def __del__(self):
        del self.map
        del self.geolocator


if __name__ == "__main__":
    TWEETS_FILE = "temp/tweets.txt"
    DIST_DIR = "dist"
    OVERLAY_DIR = "overlay-components"

    uk = Map(TWEETS_FILE, DIST_DIR)
    uk.generate_map()
    uk.add_borders()
    uk.save_map()
    uk.inject_overlay(DIST_DIR, OVERLAY_DIR)
