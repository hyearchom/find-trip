import findtrip
import os.path
import json
from random import choice
import argparse

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

#---Execution---

if __name__ == "__main__":
    args = parser.parse_args() # get line arguments
    cities = ''
    
    # cheching if same query was requested before
    history = findtrip.locate_file(HISTORY_PATH)
    if history:
        previous_finds = findtrip.read_data(HISTORY_PATH)
        cities = findtrip.return_request_from_history(args.place, args.distance, previous_finds)
    
        # if some cities were provided from the script before, they are excluded
        visited = locate_file(VISITED_PATH)
        if visited:
            exclude_cities = findtrip.read_data(VISITED_PATH)
            target_city = findtrip.choose_nonvisited_city(cities, exclude_cities)
        else:
            target_city = findtrip.choose_nonvisited_city(cities)
        
        # selected city is being displayed and saved for future exclusion from results
        findtrip.save_visited_city(target_city, visited)
        print(f"Visit '{target_city}'")
    
    else:
        print("Your request wasn't found in history. Use 'findtrip.py' instead.")