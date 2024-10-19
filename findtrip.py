#!/usr/bin/env python3
# the previous line is for unix systems and can be freely deleted
import os.path
import json
from random import choice
import sys
import argparse
import webbrowser
import folium

"""Making sure about device support, where 
Open Street Map module is hard to install
(et. mobile phones, tablets...)"""
try:
    import osmnx
    module_osmnx = True
except ModuleNotFoundError:
    module_osmnx = False

#---Settings---

# Points of interest

PLACES = {'place': ['city', 'town', 'village']}
FEATURES = {'board_type': True}

# Location of source files
SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(SCRIPT_PATH, 'settings/findtrip')
# looking for necessary folders, or creating it
os.makedirs(SETTINGS_PATH, exist_ok=True)

HISTORY_PATH = os.path.join(SCRIPT_PATH, SETTINGS_PATH, 'history.dat')
VISITED_PATH = os.path.join(SCRIPT_PATH, SETTINGS_PATH, 'visited.dat')
HOME_PATH = os.path.join(SCRIPT_PATH, SETTINGS_PATH, 'home.dat')

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


def places_within_distance_from_address(address, max_distance, places, limit=None):
    """Find all points of interest within a specified distance from a point of origin"""
    database = osmnx.features.features_from_address(
        address=address,
        dist=max_distance *1000,
        tags=places)
    
    names = []
    for record in database['name']:
        if type(record) == str:
            names.append(record)
        if limit and len(names) == limit:
            break
    return names, database


def coords_from_address(origin):
    """Ask OpenStreetMap to find coordinates of the origin"""
    center_coords = osmnx.geocoder.geocode(origin)
    if not center_coords:
        show_message_and_exit(f"<Address '{origin}' not found.>")
    return center_coords


def show_message_and_exit(message):
    print(message)
    input("Press any key to exit")
    sys.exit()


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
    if not locate_file(file_name):
        return

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
        show_message_and_exit('<Home address have been set. It will be used if place is not mentioned>')

    # use of saved home address
    if not args.place:
        home = read_data(HOME_PATH)
        if not home:
            show_message_and_exit('<Place or home have not been set>')
        args.place = home

    city_names = ''
    city_details = []
    history = read_data(HISTORY_PATH)

    # request to OpenStreetMap for data and save results
    if module_osmnx:
        city_names, city_details = places_within_distance_from_address(args.place, args.distance, PLACES)
        if not args.no_history:
            save_finds(args.place, args.distance, city_names, history)
    else:
        if history:
            city_names = return_request_from_history(args.place, args.distance, history)
        else:
            show_message_and_exit('<Query missing from history, while module OSMNX is not available>')
    
    # if some cities were selected by the script before, they are excluded
    visited = read_data(VISITED_PATH)
    target_city = choose_nonvisited_city(city_names, visited)
    
    # selected city is being saved for future exclusion from results
    if not args.no_history:
        save_visited_city(target_city, visited)

    # find target city coordinates
    target_city_coords = []
    if city_details.any:
        geometry = city_details[city_details.name == target_city].geometry
        target_city_coords = [geometry.centroid.y.iloc[0], geometry.centroid.x.iloc[0]]
    elif module_osmnx:
        target_city_coords = list(coords_from_address(target_city))

    # create map with location of the city
    map_image = folium.Map(target_city_coords, zoom_start=15)
    map_image.save(f'{target_city}.html')

    # show result
    print(f"Visit ---> '{target_city}'", end='\n\n')

    # find points of interest around target city
    if module_osmnx:
        points,_ = places_within_distance_from_address(target_city, 5, FEATURES, 5)
        for point in points:
            print(point)

    # offer display on map and exit
    try:
        input('\nPress Ctrl+C to show place on map or something else to exit')
    except KeyboardInterrupt:
        print('\n<Opening map in webrowser>')
        webbrowser.open(f'{target_city}.html')
    finally:
        print('\nHave a nice trip!')