
import json
import spacy
# from geograpy import places
from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster
NER = spacy.load("en_core_web_lg")
from tqdm import tqdm

class Map:
    def __init__(self,filename):
        self.filename = filename
        self.geolocator = Nominatim(user_agent="map ukraine")
        self.m = folium.Map(location = (48.3794, 31.1656), zoom_start=6)

    def get_words(self):
        words = []
        with open(self.filename,"r") as f:
            raw_text = f.readlines()
            for tweet in raw_text:
                tweet = tweet.strip()
                if tweet:
                    text= NER(tweet)
                    for word in text.ents:
                        if word.label_ == "GPE" or  word.label_ == "LOC":
                            # print(word.text,word.label_,end=", ")
                            words.append(word.text)
        return words

    def _get_cities_and_regions(words):
        from geograpy import places
        pc = places.PlaceContext(words)
        pc.set_countries()
        pc.set_regions()
        pc.set_cities()
        return pc.cities+pc.regions

    def generate_map(self, use_filter=True):
        marker_cluster = MarkerCluster().add_to(self.m)
        places = self.get_words()
        if not use_filter:
            places = self._get_cities_and_regions(places)
        print("Adding markers... (This may take a while)")
        for i in tqdm(places):
            geodata = self.geolocator.geocode(i)
            if geodata is not None:
                geodata = geodata.raw
                location = (geodata["lat"], geodata["lon"])
                rev = self.geolocator.reverse([geodata["lat"], geodata["lon"]]).raw
                if use_filter:
                    if rev['address']['country_code'] == 'ua':
                        folium.Marker(location=location,icon=folium.Icon(color="red", icon="exclamation-sign")).add_to(marker_cluster)
                else:
                    folium.Marker(location=location,icon=folium.Icon(color="red", icon="exclamation-sign")).add_to(marker_cluster)

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

    def save_map(self,outfile="map.html"):
        self.m.save(outfile)
    
    def __del__(self):
        del self.m
        del self.geolocator
if __name__ == "__main__":
    uk = Map("twitter.txt")
    uk.generate_map()
    uk.add_borders()
    uk.save_map()