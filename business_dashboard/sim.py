# General notes:
# All times measured in seconds since beginning of day.

import cPickle as pickle
import json
import math
import random
import logging

import biz_tools
from router import Router

inf = 1e20
zone = 'mtv'
residential_file = biz_tools.get_residential_file_name(zone)

class Robot:
    def __init__(self, avail_time, avail_loc):
        self.avail_time = avail_time
        self.avail_loc = avail_loc

class Event:
    def __init__(self, time, loc):
        self.time = time
        self.loc = loc

    def __repr__(self):
        return '(time %s, loc %s)' % (self.time, self.loc)

class Request:
    def __init__(self, time, start_loc, end_loc):
        self.time = time
        self.start_loc = start_loc
        self.end_loc = end_loc

    def __repr__(self):
        return '(time %s, start_loc %s, end_loc %s)' % (self.time, self.start_loc, self.end_loc)

    def __gt__(self, r):
        return self.time > r.time

class RequestStats:
    def __init__(self, wait_time, pickup_time, dropoff_time, required_time):
        self.wait_time = wait_time
        self.pickup_time = pickup_time
        self.dropoff_time = dropoff_time
        self.required_time = required_time

    def __repr__(self):
        return '(wait %s, pickup %s, dropoff %s, required %s)' % \
                (self.wait_time, self.pickup_time, self.dropoff_time, self.required_time)

# Use this for the sim test
def get_travel_time_dummy(start_loc, end_loc):
    return 0 if start_loc == end_loc else 1.

def get_travel_time_gmaps(start_loc, end_loc):
    a = gmaps.distance_matrix(start_loc, end_loc)
    return a['rows'][0]['elements'][0]['duration']['value']

def get_travel_time_osm(start_loc, end_loc, params, router):
    travel_time, lls = router.route(start_loc, end_loc, params)
    if lls == []: return inf
    return travel_time

def get_travel_time_heuristic(start_loc, end_loc):
    return biz_tools.latlngdist(start_loc, end_loc) / 25 * 3600

def argmin(li):
    a = [(x, i) for i, x in enumerate(li)]
    a.sort()
    return a[0][1], a[0][0]

def get_best_robot_and_time(event, robots):
    times = []
    for r in robots:
        leave_time = max(event.time, r.avail_time)
        times.append((leave_time + get_travel_time_heuristic(r.avail_loc, event.loc), leave_time))
    r_ind, (arrive_time, leave_time) = argmin(times)
    return r_ind, arrive_time, leave_time

def robot_logs_to_js(robot_logs):
    lines = [[], []]
    for l in robot_logs:
        for (e1, e2, ind) in l:
            lines[ind].append((e1.loc, e2.loc))
    with open('static/js/robot_logs.js', 'w') as f:
        f.write('var robot_logs = ' + json.dumps(lines))

def run_sim(request_list, params, router):
    num_robots = params['num_robots']
    start_wait = params['business_prep_time_min'] * 60
    end_wait = params['customer_pickup_time_min'] * 60
    request_stats = []
    robot_logs = [[] for _ in range(num_robots)]
    serviced_count = 0

    with open(residential_file, 'rb') as f:
        res_waypoints = pickle.load(f)
    robots = [Robot(0., random.choice(res_waypoints)) for _ in range(num_robots)] \
            if params['robot_start'] == 'random' else params['robot_start']

    for ind, request in enumerate(request_list):
        r_ind, arrive_time_heuristic, robot_start_time = get_best_robot_and_time(Event(request.time, request.start_loc), robots)
        r = robots[r_ind]
        arrive_time = robot_start_time + get_travel_time_osm(r.avail_loc, request.start_loc, params, router)
        if ind % 50 == 0:
            logging.info('request number %s: %s', ind, request)
            logging.info('arrive time estimate: %s, actual arrive time: %s',
                    arrive_time_heuristic, arrive_time)
        leave_time = max(arrive_time, request.time + start_wait)
        travel_time = get_travel_time_osm(request.start_loc, request.end_loc, params, router)
        final_arrive_time = leave_time + travel_time
        if arrive_time > inf/10 or final_arrive_time > inf/10:
            continue

        rlog = robot_logs[r_ind]
        rlog.append((Event(robot_start_time, r.avail_loc), Event(arrive_time, request.start_loc), 0))
        rlog.append((Event(leave_time, request.start_loc), Event(final_arrive_time, request.end_loc), 1))

        request_stats.append(RequestStats(final_arrive_time - request.time, arrive_time - robot_start_time,
            final_arrive_time - leave_time, travel_time + start_wait))
        robots[r_ind] = Robot(arrive_time + end_wait, request.end_loc)
        serviced_count += 1

    other_stats = {'service_ratio': float(serviced_count) / len(request_list)}
    return request_stats, other_stats, robot_logs

def setup_sim(params):
    with open(residential_file, 'rb') as f:
        res_waypoints = pickle.load(f)

    data = biz_tools.get_business_data(zone)
    business_locs = [(i[1], i[2]) for i in data]
    requests = []
    for i in range(params['num_requests']):
        for tries in range(10):
            end_loc = random.choice(res_waypoints)
            good_businesses = [b for b in business_locs \
                    if biz_tools.latlngdist(b, end_loc) < params['business_radius_mi']]
            if good_businesses != []: break
        if good_businesses == []: raise ValueError('No good businesses in range!')
        start_loc = random.choice(good_businesses)
        time = random.uniform(8,20) * 3600
        requests.append(Request(time, start_loc, end_loc))

    return sorted(requests)

def summarize_stats(request_stats, other_stats, params):
    def column_mean(a, i):
        return float(sum([a[j][i] for j in range(len(a))])) / len(a)

    a = [[x.wait_time, x.pickup_time, x.dropoff_time, x.required_time] for x in request_stats]
    agg_stats = {'wait_time': column_mean(a, 0) / 60, 'pickup_time': column_mean(a, 1) / 60,
            'dropoff_time': column_mean(a, 2) / 60, 'required_time': column_mean(a, 3) / 60,
            'service_ratio': other_stats['service_ratio']}
    return agg_stats

def sim_test():
    params = {'num_robots': 1, 'business_prep_time_min': 0., 'customer_pickup_time_min': 0.,
            'num_requests': 3, 'business_radius_mi': 2, 'robot_start': [Robot(0., 'x')]}
    request_list = [Request(1, 'a', 'c'), Request(2, 'a', 'b')]
    stats = run_sim(request_list, params)
    assert get_travel_time == get_travel_time_dummy
    assert all([x.__repr__() == y.__repr__() for (x,y) in zip(stats, [RequestStats(2.,2.,1.), RequestStats(3.,2.,1.)])])

def sim_end_to_end(params, router):
    logging.info('running sim with params %s', params)
    requests = setup_sim(params)
    request_stats, other_stats, robot_logs = run_sim(requests, params, router)
    agg_stats = summarize_stats(request_stats, other_stats, params)
    return agg_stats

if __name__ == '__main__':
    router = Router(False)
    params = {'num_robots': 3, 'business_prep_time_min': 20, 'customer_pickup_time_min': 5,
            'num_requests': 100, 'business_radius_mi': 2, 'robot_start': 'random',
            'robot_max_speed_mph': 60., 'road_speed_thresh_mph': 35, 'traffic_multiplier': 1.}
    sim_end_to_end(params, router)
