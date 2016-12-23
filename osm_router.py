from scrape import *

class Router:
    def __init__(self):
        node_dict, good_ways, all_ways = load_map_data()
