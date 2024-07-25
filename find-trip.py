import osmnx
from random import choice
import argparse

#---Settings---

# Line arguments
parser = argparse.ArgumentParser(
        prog='Find Trip',
        description='Get random city in given distance'
        )
parser.add_argument(
        'place',
        nargs='?',
        default="Praha",
        help="""Add center point in form of address"""
        )
parser.add_argument(
        'distance',
        type=int,
        nargs='?',
        default=20,
        help="""Set required distance in kilometers""",
        )

#---Code---

def print_random_city(origin, max_distance):
    nearby_cities = cities_within_distance(origin, max_distance)
    print(choice(nearby_cities))


def cities_within_distance(origin, max_distance):
    """Find all cities within a specified distance from a point of origin."""
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

#---Execution---

if __name__ == "__main__":
    arguments = parser.parse_args() # get line arguments
    print_random_city(arguments.place, arguments.distance)