import json

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Way, Waypoint, Business

@csrf_exempt
def index(request):
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
        #road_data.append(flatten([roads_by_speed[i] for i in ['none']])[:1000])
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
