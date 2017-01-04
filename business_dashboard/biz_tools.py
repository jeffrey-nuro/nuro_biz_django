import cPickle as pickle
import json
import math
import os
from random import shuffle

from osmread import parse_file, Way, Node

inf = 1e20
base_dir = 'business_dashboard/static/data'

def get_osm_map_name(zone):
    return os.path.join(base_dir, zone, 'map.osm')

def get_output_map_name(zone):
    return os.path.join(base_dir, zone, 'node_dict_and_good_ways.p')

def get_residential_file_name(zone):
    return os.path.join(base_dir, zone, 'residential_waypoints.p')

def get_orig_business_file_name(zone):
    return os.path.join(base_dir, zone, 'business_data_yelp_format.p')

def get_business_file_name(zone):
    return os.path.join(base_dir, zone, 'business_data.p')

def latlngdist(wp1, wp2):
    lat1, lon1 = wp1
    lat2, lon2 = wp2
    radius = 3960. # miles

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d

def make_node_dict(zone):
    node_dict = {}
    for node in parse_file(get_osm_map_name(zone)):
        if isinstance(node, Node):
            node_dict[node.id] = (node.lat, node.lon)
    return node_dict

# returns distance to line, fraction along line, and point on line
def point_to_segment(p, p1, p2):
    x, y = p
    x1, y1 = p1
    x2, y2 = p2
    x, y = x - x1, y - y1
    x2, y2 = x2 - x1, y2 - y1
    t = (x * x2 + y * y2) / (x2 * x2 + y2 * y2)
    d = ((x - t * x2)**2 + (y - t * y2)**2)**0.5
    return d, t, (p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1] - p1[1]))

def point_to_point(p, p1):
    x, y = p
    x1, y1 = p1
    return ((x-x1)**2 + (y-y1)**2)**0.5

def distinct_points(p1, p2):
    return abs(p1[0] - p2[0]) > 1e-7 or abs(p1[1] - p2[1]) > 1e-7

def point_to_way(p, way, node_dict):
    nodes = [node_dict[node_id] for node_id in way.nodes]
    closest_dist = inf
    closest_point = None

    for p1 in nodes:
        d = point_to_point(p, p1)
        if d < closest_dist:
            closest_dist = d
            closest_point = p1

    for p1, p2 in zip(nodes[:-1], nodes[1:]):
        if distinct_points(p1, p2):
            d, t, perp_p = point_to_segment(p, p1, p2)
            if t < 1 and t > 0 and d < closest_dist:
                closest_dist = d
                closest_point = perp_p
    return closest_dist, closest_point

def get_business_data(zone):
    with open(get_business_file_name(zone), 'rb') as f:
        return pickle.load(f)

def save_business_data(zone):
    with open(get_orig_business_file_name(zone), 'rb') as f:
        responses = pickle.load(f)

    data = []
    for res in responses:
        for i in res.businesses:
            name = i.name
            loc = i.location.coordinate
            if loc is None:
                continue
            lat, lng = loc.latitude, loc.longitude
            data.append((name, lat, lng, i.eat24_url))

    with open(get_business_file_name(zone), 'wb') as f:
        pickle.dump(data, f)

def make_map_data(zone):
    node_dict = make_node_dict()
    all_ways = []
    good_ways = []
    bad_count = 0
    residential_waypoints = []
    for entity in parse_file(get_osm_map_name(zone)):
        #if isinstance(entity, Way) and 'maxspeed' in entity.tags:
        if isinstance(entity, Way):
            if len(entity.nodes) < 2: continue
            if 'highway' not in entity.tags: continue
            all_ways.append(entity)
            if 'maxspeed' in entity.tags:
                good_ways.append(entity)
            for nid in entity.nodes:
                residential_waypoints.append(node_dict[nid])

    with open(get_ouput_map_name(zone), 'wb') as f:
        pickle.dump((node_dict, good_ways, all_ways), f)

    with open(get_residential_file_name(zone), 'wb') as f:
        pickle.dump(residential_waypoints, f)

def load_map_data(zone):
    with open(get_output_map_name(zone), 'rb') as f:
        node_dict, good_ways, all_ways = pickle.load(f)
    return node_dict, good_ways, all_ways

def process_businesses():

    business_data = get_business_data()
    node_dict, good_ways, all_ways = load_map_data()
    final_data = []

    for (name, lat, lng, _) in business_data:
        print name
        min_dist = inf
        best_p = None
        count = 0
        for way in good_ways:
            count += 1
            d, p = point_to_way((lat, lng), way, node_dict)
            if d < min_dist:
                min_dist = d
                best_p = p
                speed = way.tags['maxspeed'] if 'maxspeed' in way.tags else 'none'
        final_data.append([name, lat, lng, best_p[0], best_p[1], speed, min_dist])

    with open('static/js/business_data.js', 'w') as f:
        f.write('var business_data = ' + json.dumps(final_data))
    return final_data

def flatten_and_shuffle(li):
    a = [i for l in li for i in l]
    shuffle(a)
    return a

def flatten(li):
    return [i for l in li for i in l]

def process_speed_limits():
    node_dict, good_ways, all_ways = load_map_data()
    roads_by_speed = {}
    for way in all_ways:
        ms = way.tags['maxspeed'] if 'maxspeed' in way.tags else 'none'
        if ms not in roads_by_speed:
            roads_by_speed[ms] = []
        roads_by_speed[ms].append([node_dict[i] for i in way.nodes])

    output_arrays = []
    #output_arrays.append(flatten([roads_by_speed[i] for i in ['none']])[:1000])
    output_arrays.append([])
    output_arrays.append(flatten([roads_by_speed[i] for i in ['5 mph', '10 mph', '15 mph', '20 mph', '25 mph']]))
    output_arrays.append(flatten([roads_by_speed[i] for i in ['30 mph', '35 mph']]))
    output_arrays.append(flatten([roads_by_speed[i] for i in ['40 mph', '45 mph']]))
    output_arrays.append(flatten([roads_by_speed[i] for i in ['50 mph', '55 mph', '65 mph']]))
    with open('static/js/roads_by_speed_limit.js', 'w') as f:
        f.write('var roads_by_speed_limit = ' + json.dumps(output_arrays))

if __name__ == '__main__':
    pass

    # To generate data for a new region, use these functions:
    # save_business_data()
    # make_map_data()
    # process_businesses()
    # process_speed_limits()
