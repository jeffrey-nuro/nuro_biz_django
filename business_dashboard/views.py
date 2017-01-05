import json
import os
import sys
import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'business_dashboard'))
from router import Router
import sim
router = Router('mtv')

@csrf_exempt
def route(request):
    """Handles post request for shortest path computation"""
    if request.method == 'POST':
        post_data = request.POST
        speed_thresh = float(post_data['speed_thresh'].strip())
        try:
            traffic_multiplier = float(post_data['traffic_multiplier'].strip())
        except ValueError:
            traffic_multiplier = 1.

        route_latlngs = json.loads(post_data['route_latlngs'])
        params = {'road_speed_thresh_mph': speed_thresh,
                'traffic_multiplier': traffic_multiplier}
        dist, lls = router.route(route_latlngs[0], route_latlngs[1], params)
        logging.info('route: %s %s' % (dist, lls))
        return HttpResponse(
            json.dumps({'route': lls, 'dist': dist}),
            content_type="application/json",
        )

@csrf_exempt
def reachable_region(request):
    """Handles post request for reachable region computation"""
    if request.method == 'POST':
        post_data = request.POST
        latlngs = json.loads(post_data['latlngs'])
        radius = float(post_data['radius'].strip())
        all_points_arr, all_hulls_arr = [], []
        for speed_thresh in [65, 45, 35, 25]:
            points_arr, hull_arr = [], []
            for latlng in latlngs:
                params = {'road_speed_thresh_mph': speed_thresh, 'traffic_multiplier': 1.5}
                points, hull = router.reachable_region(latlng, radius, params)
                points_arr.extend(points)
                hull_arr.append(hull)
            all_points_arr.append(points_arr)
            all_hulls_arr.append(hull_arr)
        return HttpResponse(
            json.dumps({'hull_arr': all_hulls_arr, 'points_arr': all_points_arr}),
            content_type="application/json",
        )

@csrf_exempt
def simulate(request):
    """Handles post request for running a simulation"""
    if request.method == 'POST':
        post_data = request.POST
        params = {i: post_data[i] for i in post_data}
        logging.info(params)
        for i in ['num_robots', 'num_requests']:
            params[i] = int(params[i])
        for i in ['business_prep_time_min', 'customer_pickup_time_min', 'business_radius_mi',
                'robot_max_speed_mph', 'road_speed_thresh_mph', 'traffic_multiplier']:
            params[i] = float(params[i])
        agg_stats = sim.sim_end_to_end(params, router)
        for i in agg_stats:
            if isinstance(agg_stats[i], float):
                agg_stats[i] = '%.2f' % agg_stats[i]
        return HttpResponse(
            json.dumps(agg_stats),
            content_type="application/json",
        )

@csrf_exempt
def index(request):
    return render(request, 'business_dashboard/index.html', {})
