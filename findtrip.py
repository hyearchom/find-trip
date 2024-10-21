#!/usr/bin/env python3
# the previous line is for unix systems and can be freely deleted
import os.path
import json
from random import choice
import sys
import argparse
import webbrowser
import folium

"""Making sure about device support, where Open Street Map module is hard to install
(et. mobile phones, tablets...)"""
try:
    import osmnx
    module_osmnx = True
except ModuleNotFoundError:
    module_osmnx = False

#---Settings---

# Constants
CITY_TAGS = {'place': ['city', 'town', 'village']} # tag to identify target center point
POINT_TAGS = {'board_type': True} # tag to identify point of interest
POINT_DISTANCE = 3 # distance for points of interested from target city in km
MAP_ZOOM = 14 # default map close up in browser
CITY_MARKER_COLOR = 'red' # color to mark target city
POINT_MARKER_COLOR = 'green' # color to mark points of interest

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
    description='Show random city in given distance and tourism points around on map'
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

def choose_unvisited_city(options, exclude=None):
    """Random selection of the city from possible targets, excluding
    already visited cities if they are any"""
    if exclude:
        selection = [i for i in options if i not in exclude]
        print('<Avoiding visited cities>')
    else:
        selection = options
    return choice(selection)


def cities_within_distance_from_address(address, max_distance):
    """Find all points of interest within a specified distance from a point of origin"""
    database = osmnx.features.features_from_address(
        address=address,
        dist=max_distance *1000,
        tags=CITY_TAGS)
    return database


def points_within_distance_from_cords(cords, max_distance):
    """Find all points of interest within a specified distance from a point of origin"""
    database = osmnx.features_from_point(
        center_point=cords,
        dist=max_distance *1000,
        tags=POINT_TAGS)
    return database


def names_from_database(database):
    """Return all names from GeoDataFrame object"""
    result = []
    for record in database['name']:
        if type(record) == str:
            result.append(record)
    return result


def cords_from_address(origin):
    """Ask OpenStreetMap to find coordinates of the origin"""
    center_cords = osmnx.geocoder.geocode(origin)
    if not center_cords:
        show_message_and_exit(f"<Address '{origin}' not found.>")
    return center_cords


def show_message_and_exit(message):
    """Exit execution with a message for a user"""
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
    """Reading data from files on disk"""
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


def cords_from_database(name, database):
    """Extracting longitude and latitude of targeted record
     from given GeoDataFrame object, commonly given by osmnx module"""
    geometry = database[database.name == name].geometry.iloc[0]
    cords = cords_from_geometry(geometry)
    return cords


def cords_from_geometry(geometry):
    """Extracting longitude and latitude from Point object"""
    return [geometry.centroid.y, geometry.centroid.x]


def add_marker_to_map(cords, name, map, type='blue'):
    """Add marked position into the given map with optional color"""
    folium.Marker(
        location=cords,
        tooltip="Click for details",
        popup=name,
        icon=folium.Icon(color=type),
    ).add_to(map)


#---Execution---

if __name__ == "__main__":
    # extract line arguments from user
    args = parser.parse_args()

    # if setting home was requested by user, only this block is being executed
    if args.home:
        save_home_address(args.home)
        show_message_and_exit('<Home address have been set. It will be used if place is not mentioned>')

    # use of saved home address if place is not provided by user
    if not args.place:
        home = read_data(HOME_PATH)
        if not home:
            show_message_and_exit('<Place or home have not been set>')
        args.place = home

    # search for random target city
    city_names = ''
    city_details = []
    history = read_data(HISTORY_PATH)

    if module_osmnx:
        city_details = cities_within_distance_from_address(args.place, args.distance)
        city_names = names_from_database(city_details)
        if not args.no_history:
            save_finds(args.place, args.distance, city_names, history)
    else:
        if history:
            city_names = return_request_from_history(args.place, args.distance, history)
        else:
            show_message_and_exit('<Query missing from history, while module OSMNX is not available>')
    
    # if some cities were selected by the script before, they are excluded
    visited = read_data(VISITED_PATH)
    target_city = choose_unvisited_city(city_names, visited)
    
    # selected city is being saved for future exclusion from results
    if not args.no_history:
        save_visited_city(target_city, visited)

    # show result
    print(f"Visit ---> '{target_city}'", end='\n\n')

    # find target city coordinates
    target_city_cords = []
    if city_details.any:
        target_city_cords = cords_from_database(target_city, city_details)
    else:
        # end of execution without osmnx module (phones, tablets...)
        show_message_and_exit('<Cannot offer more details without osmnx module>')

    # create map with location of the city
    local_map = folium.Map(target_city_cords, zoom_start=MAP_ZOOM)
    add_marker_to_map(target_city_cords, target_city, local_map, CITY_MARKER_COLOR)

    # find points of interest around target city
    point_details = points_within_distance_from_cords(tuple(target_city_cords), POINT_DISTANCE)
    for row in point_details.itertuples():
        name = row.name
        location = cords_from_geometry(row.geometry)
        add_marker_to_map(location, name, local_map, POINT_MARKER_COLOR)
        # display name of point if possible
        if type(name) is str:
            print(name)

    # save map on disk
    map_path = os.path.join(SETTINGS_PATH, f'{target_city}.html')
    local_map.save(map_path)

    # offer display of map and exit
    print('\nHave a nice trip!')
    input('\nPress Ctrl+C to exit, or anything else to display map ')
    webbrowser.open(map_path)