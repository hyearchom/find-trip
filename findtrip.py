import os.path
import json
from email.policy import default
from random import choice
import sys
import argparse
import webbrowser

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
DATA_PATH = 'settings'
HISTORY_PATH = os.path.join(FILE_PATH, DATA_PATH, 'findtrip_history.dat')
VISITED_PATH = os.path.join(FILE_PATH, DATA_PATH, 'findtrip_visited.dat')
HOME_PATH = os.path.join(FILE_PATH, DATA_PATH, 'findtrip_home.dat')

# Line args
parser = argparse.ArgumentParser(
    prog='Find Trip',
    description='Get random city in given distance'
    )
parser.add_argument(
    '-p', '--place',
    help="""Add center point in form of address"""
    )
parser.add_argument(
    '-d', '--distance',
    type=int,
    default=20,
    help="""Set required distance in kilometers""",
    )
parser.add_argument(
    '--home',
    help="""Save permanent center point in form of address"""
    )
parser.add_argument(
    '-n', '--no_history',
    action='store_true',
    help="""Prevent script from saving anything into data folder after search"""
    )


#---Code---

def choose_nonvisited_city(options, exclude=None):
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
        if container:
            return json.loads(container.format(records))
        else:
            # deleting unwanted characters from address
            records = records.replace('\n', '')
            records = records.strip()
            return records


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
    as visited and omitted from future results"""
    with open(VISITED_PATH, "a", newline="") as file:    
        # JSON dumps is not used for better file readability
        if file_present:
            file.write(',\n')
        record = f"\"{city}\""
        file.write(record)


def save_home_address(address):
    """Saving chosen city provided by script. That city is considered
    as visited and omitted from future results"""
    with open(HOME_PATH, "w", newline="") as file:
        file.write(address)


#---Execution---

if __name__ == "__main__":
    args = parser.parse_args() # get line arguments

    # if setting home was initialized
    if args.home:
        save_home_address(args.home)
        sys.exit('<Home address have been set and will be used, if place is not mentioned>')

    # use of saved home address
    if not args.place:
        home = read_data(HOME_PATH)
        if not home:
            sys.exit('<Place or home have not been set>')
        args.place = home
    
    # cheching if same query was requested before
    cities = ''
    history = locate_file(HISTORY_PATH)
    if history:
        previous_finds = read_data(HISTORY_PATH)
        cities = return_request_from_history(args.place, args.distance, previous_finds)
    
    # if query is new, request to OpenStreetMap for data and save results
    if not cities:
        if MODULE_OSMNX:
            cities = cities_within_distance(args.place, args.distance)
            if not args.no_history:
                save_finds(args.place, args.distance, cities, history)
        else:
            sys.exit('<Query missing from history, while module OSMNX is not available>')
    
    # if some cities were selected by the script before, they are excluded
    visited = locate_file(VISITED_PATH)
    if visited:
        exclude_cities = read_data(VISITED_PATH)
        target_city = choose_nonvisited_city(cities, exclude_cities)
    else:
        target_city = choose_nonvisited_city(cities)
    
    # selected city is being displayed and saved for future exclusion from results
    
    print(f"Visit ---> '{target_city}'")
    webbrowser.open(f'https://www.openstreetmap.org/search?query={target_city}')

    if not args.no_history:
        save_visited_city(target_city, visited)