import cPickle as pickle
import json
from random import shuffle

from osmread import parse_file, Way, Node

from business_dashboard.models import Way as Way_db
from business_dashboard.models import Waypoint as Waypoint_db
from business_dashboard.models import Business as Business_db
from business_dashboard.models import WaypointOrder as WaypointOrder_db

from django.db import transaction

inf = 1e20
map_name = 'full_mtv.osm'
map_file_name = 'node_dict_and_good_ways.p'

def make_node_dict():
    node_dict = {}
    for node in parse_file(map_name):
        if isinstance(node, Node):
            node_dict[node.id] = (node.lat, node.lon)
    return node_dict

# TODO: if very inaccurate, use latlng->xy converter first

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

def get_business_data():
    business_file_name = 'business_data.p'
    with open(business_file_name, 'rb') as f:
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
    return data

def make_map_data():
    node_dict = make_node_dict()
    all_ways = []
    good_ways = []
    for entity in parse_file(map_name):
        #if isinstance(entity, Way) and 'maxspeed' in entity.tags:
        if isinstance(entity, Way):
            all_ways.append(entity)
            if 'maxspeed' in entity.tags:
                good_ways.append(entity)

    with open(map_file_name, 'wb') as f:
        pickle.dump((node_dict, good_ways, all_ways), f)

def load_map_data():
    with open(map_file_name, 'rb') as f:
        node_dict, good_ways, all_ways = pickle.load(f)
    return node_dict, good_ways, all_ways

def process_businesses():

    Business_db.objects.all().delete()
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
        ll = Waypoint_db(lat=lat, lng=lng)
        ll.save()
        ll2 = Waypoint_db(lat=best_p[0], lng=best_p[1])
        ll2.save()
        b = Business_db(name=name, loc=ll, street_loc=ll2, speed_limit=speed)
        b.save()

    return final_data

@transaction.atomic
def process_ways():
    node_dict, good_ways, all_ways = load_map_data()
    node_dict_db = {}
    count = 0
    Way_db.objects.all().delete()
    Waypoint_db.objects.all().delete()

    for nid in node_dict:
        count += 1
        if count % 10000 == 0:
            print 'waypoints', count
        node = node_dict[nid]
        wp = Waypoint_db(lat=node[0], lng=node[1], osm_id=nid)
        wp.save()
        node_dict_db[nid] = wp

    count = 0
    for way in good_ways:
        count += 1
        if count % 10000 == 0:
            print 'ways', count
        speed = way.tags['maxspeed'] if 'maxspeed' in way.tags else 'none'
        way_db = Way_db(speed_limit=speed)
        way_db.save()
        #way_db.waypoints.add(*[node_dict_db[i] for i in way.nodes])
        for ind, i in enumerate(way.nodes):
            WaypointOrder_db.objects.create(way=way_db, waypoint=node_dict_db[i], number=ind)
        way_db.save()
        for wp in way_db.waypoints.all():
            wp.ways.add(way_db)
            wp.save()

def flatten_and_shuffle(li):
    a = [i for l in li for i in l]
    shuffle(a)
    return a

def flatten(li):
    return [i for l in li for i in l]

def process_speed_limits():
    node_dict, good_ways, all_ways = load_map_data()
    roads_by_speed = {}
    for way in good_ways:
        ms = way.tags['maxspeed'] if 'maxspeed' in way.tags else 'none'
        if ms not in roads_by_speed:
            roads_by_speed[ms] = []
        roads_by_speed[ms].append([node_dict[i] for i in way.nodes])

    output_arrays = []
    output_arrays.append(flatten([roads_by_speed[i] for i in ['none']])[:1000])
    output_arrays.append(flatten([roads_by_speed[i] for i in ['5 mph', '10 mph', '15 mph', '20 mph', '25 mph']]))
    output_arrays.append(flatten([roads_by_speed[i] for i in ['30 mph', '35 mph']]))
    output_arrays.append(flatten([roads_by_speed[i] for i in ['40 mph', '45 mph']]))
    output_arrays.append(flatten([roads_by_speed[i] for i in ['50 mph', '55 mph', '65 mph']]))
    with open('static/js/roads_by_speed_limit.js', 'w') as f:
        f.write('var roads_by_speed_limit = ' + json.dumps(output_arrays))

if __name__ == '__main__':
    #make_map_data()
    #process_businesses()
    process_ways()
