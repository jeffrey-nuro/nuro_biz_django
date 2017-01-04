import json

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Way, Waypoint, Business

@csrf_exempt
def index(request):
    if request.method == 'POST':
        post_data = self.request.POST
        mode = post_data['mode']
        if mode == 'route':
            speed_thresh = float(post_data['speed_thresh'].strip())
            try:
                traffic_multiplier = float(post_data['traffic_multiplier'].strip())
            except ValueError:
                traffic_multiplier = 1.

            route_latlngs = json.loads(post_data['route_latlngs'])
            params = {'road_speed_thresh_mph': speed_thresh, 'traffic_multiplier': traffic_multiplier}

            dist, lls = router.route(route_latlngs[0], route_latlngs[1], params)
            print dist, lls
            self.response.write(json.dumps({'route': lls, 'dist': dist}))
            return
        if mode == 'reachable_region':
            print post_data
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
            data = {'hull_arr': all_hulls_arr, 'points_arr': all_points_arr}
            self.response.write(json.dumps(data))
            return
        if mode == 'sim':
            params = post_data
            for i in ['num_robots', 'num_requests']:
                params[i] = int(params[i])
            for i in ['business_prep_time_min', 'customer_pickup_time_min', 'business_radius_mi',
                    'robot_max_speed_mph', 'road_speed_thresh_mph', 'traffic_multiplier']:
                params[i] = float(params[i])
            agg_stats = sim.sim_end_to_end(params, router)
            for i in agg_stats:
                if isinstance(agg_stats[i], float):
                    agg_stats[i] = '%.2f' % agg_stats[i]
            self.response.write(json.dumps(agg_stats))
            return
    else:
        return render(request, 'business_dashboard/index.html', {})

def old_index(request):
    if request.method == 'POST':
        businesses = Business.objects.all()
        business_data = [[b.name, b.loc.lat, b.loc.lng, b.street_loc.lat, b.street_loc.lng, b.speed_limit] \
                for b in businesses]
        def flatten(li):
            return [i for l in li for i in l]

        roads_by_speed = {}
        all_ways = Way.objects.all()
        for way in all_ways:
            ms = way.speed_limit
            if ms not in roads_by_speed:
                roads_by_speed[ms] = []
            roads_by_speed[ms].append([[wp.lat, wp.lng] for wp in way.waypoints.all()])

        print roads_by_speed.keys()
        road_data = [[]]
        road_data.append(flatten([roads_by_speed[i] for i in ['none']])[:1000])
        road_data.append(flatten([roads_by_speed[i] for i in ['5 mph', '10 mph', '15 mph', '20 mph', '25 mph']]))
        road_data.append(flatten([roads_by_speed[i] for i in ['30 mph', '35 mph']]))
        road_data.append(flatten([roads_by_speed[i] for i in ['40 mph', '45 mph']]))
        road_data.append(flatten([roads_by_speed[i] for i in ['50 mph', '55 mph', '65 mph']]))
        return HttpResponse(
            json.dumps({'roads': road_data, 'businesses': business_data}),
            content_type="application/json",
        )
    else:
        return render(request, 'business_dashboard/index.html', {})
