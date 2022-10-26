import re
import typer
import googlemaps
import time
import pandas as pd
import inspect
#import sys
import requests
import scrapy
from scrapy_splash import SplashRequest
import scrapy_splash
import json

def objinfo(obj):
    for i in dir(obj):
       print(i, getattr(obj, i))

def defaults(defawlt):
    #defult = input("Please enter a value for {}: ".format(defawlt))
    #try:
    #    defult = int(defult)
    #finally:
    #    return defult
    return input("Please enter a value for {}: ".format(defawlt))

def main(startpoint: str="", radius: int=0, search_string: str="", key: str=""):
    args = vars()
    typer.echo(f"Hello! Would you like a job?")

    argspec=inspect.getargvalues(inspect.currentframe())
    for arg in argspec.args:
        if args[arg] == "" or args[arg] == 0:
            args[arg] = defaults(arg)
    df = places(args["key"], args["startpoint"], args["search_string"], args["radius"])
    #df = pd.read_excel('tmp.xlsx')
    (sites, failures) = list_websites(df, args['key'])
    #print(sites)
    #print(failures)
    final_locations = []
    for i in sites:
        if i[0] != None:
            uri = find_landing(i[0])
            print("At {}, we found {}".format(df['name'][i[2]],"{}{}".format(uri[0],uri[1])))
            final_locations.append(uri[1])
    print("\n\nHere is your to-dos: ")
    for i in final_locations:
        print(i)

def rate_limiting(rate):
    print("Got rate limited, chillin for a bit")
    time.sleep(1+rate)
    print("Ok back to work")


def find_landing(site): #currently fails with some dynamic sites
    landingsfile = open('joblandings.txt', 'r')
    landingslist = landingsfile.read().split('\n')
    for i in landingslist:
        #print(i, site)
        try:
            #print("trying {}".format("{}{}".format(site, i)))
            response = requests.head("{}{}".format(site, i))
            #print("got {}".format(response.status_code))
            while response.status_code == 429:
                i = 0
                rate_limiting(i)
                response = requests.head("{}{}".format(site, i))
                i += 2
                if i >= 20:
                    break
            if response.status_code >= 300 and response.status_code < 400:
                response = requests.head(re.sub(r"http:\/\/","https://","{}{}".format(site, i)))
                
        except requests.ConnectionError as e:
            #print("Connection error: {}".format(e))
            pass
        
        if response.status_code == 200:
            return ("job landing: ","{}{}".format(site, i))
    return ("no job landing, just ","{}".format(site))

def list_websites(df, key):
    sites = []
    failures = []
    for i in range(0, len(df)):
            sites.append((json.loads(retrieve_website(key, df['place_id'][i]).text)["result"].get("website"), df['place_id'][i], i))
            if sites[-1] == None:
                print("Location {} does not have a listed website, adding to failures.".format(df['name'][i]))
                failures.append(df['place_id'][i])
                sites.pop()
    return (sites, failures)

def crawl(url):
    #res = yield requests.get(url)
    #print(res)
    print("test")
    yield SplashRequest(url, self.parse_result,
    args={
        # optional; parameters passed to Splash HTTP API
        'wait': 0.5,

        # 'url' is prefilled from request url
        # 'http_method' is set to 'POST' for POST requests
        # 'body' is set to request body for POST requests
    },
    endpoint='render.json', # optional; default is render.html
    splash_url='<url>',     # optional; overrides SPLASH_URL
    slot_policy=scrapy_splash.SlotPolicy.PER_DOMAIN,  # optional
    )

def retrieve_website(key, placeid):
    #currently requests too many fields that are not used
    url = "https://maps.googleapis.com/maps/api/place/details/json?place_id={}&fields=name%2Crating%2Cwebsite&key={}".format(placeid, key)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response

def places(key, startpoint, search_string, radius):
    gmaps = googlemaps.Client(key)
    geo = gmaps.geocode(address=startpoint)
    (lat, lng) = map(geo[0]['geometry']['location'].get, ('lat', 'lng'))
    response = gmaps.places_nearby(
            location=(lat, lng),
            keyword=search_string,
            radius=int(radius) * 1_609.344
    )
    places = []
    places.extend(response.get('results'))
    token = response.get('next_page_token')
    while token:
        time.sleep(2)
        response = gmaps.places_nearby(
            location=(lat, lng),
            keyword=search_string,
            radius=int(radius) * 1_609.344,
            page_token=token
        )
        places.extend(response.get('results'))
        token = response.get('next_page_token')
    df = pd.DataFrame(places)
    df['url'] = 'https://www.google.com/maps/place/?q=place_id:' + df['place_id']
    df.to_excel('{0}.xlsx'.format(search_string), index=False)
    return pd.read_excel('{0}.xlsx'.format(search_string))

if __name__ == "__main__":
    typer.run(main) 