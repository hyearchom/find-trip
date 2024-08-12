import os.path
import json
from random import choice
import sys
import argparse

"""Making sure about device support, where 
Open Street Map module is hard to install
(et. mobile phones, tablets...)"""
MODULE_OSMNX = True
try:
    import osmnx
except:
    MODULE_OSMNX = False

#---Settings---

# Location of source files
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
HISTORY_PATH = os.path.join(FILE_PATH, 'findtrip_history.dat')
VISITED_PATH = os.path.join(FILE_PATH, 'findtrip_visited.dat')

# Line args
parser = argparse.ArgumentParser(
        prog='Find Trip',
        description='Get random city in given distance'
        )
parser.add_argument(
        '-p', '--place',
        default="New York",
        help="""Add center point in form of address"""
        )
parser.add_argument(
        '-d', '--distance',
        type=int,
        default=20,
        help="""Set required distance in kilometers""",
        )

#---Code---

def choose_nonvisited_city(options, exclude=[]):
    """Random selection of the city from possible targets, excluding
    already visited cities if they are any"""
    if exclude:
        selection = [i for i in options if i not in exclude]
        print('<Avoiding visited cities>')
    else:
        selection = options
    return choice(selection)


def cities_within_distance(origin, max_distance):
    """Find all cities within a specified distance from a point of origin"""
    # Ask OpenStreetMap to find coordinates of the origin
    center_coords = osmnx.geocoder.geocode(origin)
    if not center_coords:
        return f"Address '{origin}' not found."
    
    # Ask OpenStreetMap for cities, towns, and villages within the bounding box
    database = osmnx.features.features_from_point(
            center_coords, 
            dist=max_distance *1000,
            tags={'place': ['city', 'town', 'village']})
    
    # Filter the results by actual distance
    nearby_cities = []
    for _, row in database.iterrows():
        city_name = row.get('name')
        city_coords = (row.geometry.centroid.y, row.geometry.centroid.x)
        distance = osmnx.distance.great_circle(*center_coords, *city_coords) /1_000.0
        if distance < max_distance:
            nearby_cities.append(city_name)    
    return nearby_cities


def save_finds(center, limit, array, file_present):
    """Saving OpenStreetMap output for later use"""
    with open(HISTORY_PATH, "a", newline="") as file:
        # writing visual and code division
        if file_present:
            file.write(',\n\n')    
        # JSON dumps is not used for better file readability
        array = str(array).replace("'", r'"')
        record = f"\"{center}; {limit}\": {array}"""
        file.write(record)


def read_data(file_name):
    """Reading data from data files"""
    container = ''
    if file_name == HISTORY_PATH:
        container = '{{{}}}'
    elif file_name == VISITED_PATH:
        container = '[{}]'

    with open(file_name, "r", newline="") as file:
        records = file.read()
    return json.loads(container.format(records)) # JSON is used for code safety


def locate_file(path):
    """Checking if data file has been generated before"""
    return os.path.isfile(path)


def return_request_from_history(center, limit, finds):
    """Checking history data if same query has been
    searched and saved into memory before, returning
    any result or empty string"""
    name = f'{center}; {limit}'
    if name in finds:
        print('<Using saved history>')
        return finds[name]
    else:
        return ''


def save_visited_city(city, file_present):
    """Saving chosen city provided by script. That city is considered
    as visited and omited from future results"""
    with open(VISITED_PATH, "a", newline="") as file:    
        # JSON dumps is not used for better file readability
        if file_present:
            file.write(',\n')
        record = f"\"{city}\""
        file.write(record)


#---Execution---

if __name__ == "__main__":
    args = parser.parse_args() # get line arguments
    cities = ''
    
    # cheching if same query was requested before
    history = locate_file(HISTORY_PATH)
    if history:
        previous_finds = read_data(HISTORY_PATH)
        cities = return_request_from_history(args.place, args.distance, previous_finds)
    
    # if query is new, request to OpenStreetMap for data and save results
    if not cities:
        if MODULE_OSMNX:
            cities = cities_within_distance(args.place, args.distance)
            save_finds(args.place, args.distance, cities, history)
        else:
            sys.exit('<Query missing from history, while module OSMNX is not available>')
    
    # if some cities were provided from the script before, they are excluded
    visited = locate_file(VISITED_PATH)
    if visited:
        exclude_cities = read_data(VISITED_PATH)
        target_city = choose_nonvisited_city(cities, exclude_cities)
    else:
        target_city = choose_nonvisited_city(cities)
    
    # selected city is being displayed and saved for future exclusion from results
    save_visited_city(target_city, visited)
    print(f"Visit ---> '{target_city}'")