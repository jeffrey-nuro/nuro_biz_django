// This file has the code responsible for parsing AJAX response JSON
// and rendering the leaflet map layers.

var waypoint_displays = []
var wayline_displays = []
var polygon_displays = [];
var stale_polygons = false;

var wayline_styles = [
    {opacity: 1},
    {opacity: 1, color: 'gray'},
    {opacity: 1, color: 'green'},
    {opacity: 1, color: 'yellow'},
    {opactiy: 1, color: 'orange'},
    {opactiy: 1, color: 'red'},
    {opacity: 1, color: 'purple', weight: 4},
    {opacity: 1, color: 'purple', weight: 10},
]

var polygon_styles = [
    {color: 'white'},
    {color: 'red', weight: 0, fillOpacity: 0.5},
    {color: 'orange', weight: 0, fillOpacity: 0.5},
    {color: 'yellow', weight: 0, fillOpacity: 0.5},
    {color: 'green', weight: 0, fillOpacity: 0.5},
]

function in_range(point, latlng_range) {
    return point[0] > latlng_range[0] && point[0] < latlng_range[1] && point[1] > latlng_range[2] && point[1] < latlng_range[3];
}

function speed_limit_to_point_type(speed_str) {
    switch(speed_str) {
        case '5 mph': return '<=25';
        case '10 mph': return '<=25';
        case '15 mph': return '<=25';
        case '20 mph': return '<=25';
        case '25 mph': return '<=25';
        case '30 mph': return '<=35';
        case '35 mph': return '<=35';
        case '40 mph': return '<=45';
        case '45 mph': return '<=45';
        default: return 'all';
    }
}

function data_to_waypoints(data) {
    var waypoints = {
        'type': 'FeatureCollection',
        'features': []
    }
    for (var i = 0; i<data.length; i++) {
        waypoints.features.push({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [
                    data[i][1], data[i][0]
                ]
            },
            'properties': {
                //'selected': (data[i][2] == 1),
                'point_type': data[i][2],
                'angle': data[i][3],
            },
            'id': i
        });
    }

    return waypoints;
}

function data_to_splines(components) {

    zoom = map._zoom;
    var points_set = []
    for (var set_ind = 0; set_ind < components.length; set_ind++) {
        points = [];
        spline_set = components[set_ind];
        for (var i = 0; i<spline_set.length; i++) {
            points.push(spline_set[i]);
        }
        points_set.push(points);
    }

    return points_set;
}

function business_data_points_and_lines(latlng_range) {
    var points = [];
    var lines = [];
    for (var i = 0; i < business_data.length; ++i) {
        bd = business_data[i];
        if (in_range([bd[1], bd[2]], latlng_range) && in_range([bd[3], bd[4]], latlng_range)) {
            points.push([bd[1], bd[2], speed_limit_to_point_type(bd[5]), 0]);
            points.push([bd[3], bd[4], 'none', 0]);
            lines.push([[bd[1], bd[2]], [bd[3], bd[4]]]);
        }
        if (points.length > max_business_display_num) {
            break;
        }
    }
    return [points, [lines]];
}

function draw() {
    map.removeLayer(waypoint_displays);

    var mb = map.getBounds();
    var min_lat = Math.max(mb._southWest.lat, business_bounds[0]);
    var min_lng = Math.max(mb._southWest.lng, business_bounds[1]);
    var max_lat = Math.min(mb._northEast.lat, business_bounds[2]);
    var max_lng = Math.min(mb._northEast.lng, business_bounds[3]);
    var latlng_range = [min_lat, max_lat, min_lng, max_lng];

    var points_and_lines = business_data_points_and_lines(latlng_range);
    var points = points_and_lines[0];
    var lines = points_and_lines[1];

    if (route_latlngs.length > 0) {
        points.push([route_latlngs[0][0], route_latlngs[0][1], 'route_start']);
    }

    if (route_latlngs.length > 1) {
        points.push([route_latlngs[1][0], route_latlngs[1][1], 'route_end']);
    }

    for (var i = 0; i < reachable_latlngs.length; ++i) {
        points.push([reachable_latlngs[i][0], reachable_latlngs[i][1], 'route_end']);
    }

    /*
     * Uncomment this to display reachable points, not just their convex hull.
     * It doesn't look good with the overlay though.
     *
    if (reachable_points.length > 0) {
        for (var i = 0; i < reachable_points.length; ++i) {
            var pts = reachable_points[i];
            var ptype = '<=25';
            if (i == 1) {
                ptype = '<=35';
            } else if (i == 2) {
                ptype = '<=45';
            } else {
                ptype = 'all';
            }

            for (var j = 0; j < pts.length; ++j) {
                points = points.concat([pts[j][0], pts[j][1], ptype]);
            }
        }
    }
    */

    waypoints = data_to_waypoints(points);

    wayline_data = data_to_splines(lines);
    wayline_data = wayline_data.concat(roads_by_speed_limit);
    wayline_data.push(disp_route);

    selected_ind = -1;
    var min_lat = business_bounds[0];
    var min_lng = business_bounds[1];
    var max_lat = business_bounds[2];
    var max_lng = business_bounds[3];

    if (drawn_once) {
        for (var i = 0; i < polygons.length; ++i) {
            for (var j = 0; j < polygons[i].length; ++j) {
                try {
                    map.removeLayer(polygon_displays[i][j]);
                } catch (err) {
                }
            }
        }
    }

    polygons = [[[[min_lat, min_lng], [min_lat, max_lng], [max_lat, max_lng], [max_lat, min_lng]]]];
    if (reachable_polygons.length > 0) {
        polygons = polygons.concat(reachable_polygons);
    }

    for (var i = 0; i < polygons.length; ++i) {
        for (var j = 0; j < polygons[i].length; ++j) {
            if (!polygon_displays[i]) {
                polygon_displays[i] = [];
            }

            if (i == polygons.length-1) {
                polygon_displays[i][j] = L.polygon(polygons[i][j], polygon_styles[i]);
            } else {
                var polygon_and_holes = [polygons[i][j], polygons[i+1][j]];
                console.log(polygon_and_holes);
                polygon_displays[i][j] = L.polygon(polygon_and_holes, polygon_styles[i]);
            }
            if (polygons[i][j].length > 3) {
                polygon_displays[i][j].addTo(map);
            }
        }
    }

    waypoint_displays = L.geoJson(waypoints, {
        style: function (feature) {
            return feature.properties && feature.properties.style;
        },

        pointToLayer: function (feature, latlng) {
            var ptype = feature.properties.point_type;
            if (ptype == '<=25') {
                fill = 'green';
                rad = 6;
            } else if (ptype == '<=35') {
                fill = 'yellow';
                rad = 6;
            } else if (ptype == '<=45') {
                fill = 'orange';
                rad = 6;
            } else if (ptype == 'all') {
                fill = 'red';
                rad = 6;
            } else if (ptype == 'route_start') {
                fill = '#ff00ff';
                rad = 6;
            } else if (ptype == 'route_end') {
                fill = 'pink';
                rad = 12;
            } else {
                fill = 'blue';
                rad = 4;
            }
            return L.circleMarker(latlng, {
                radius: rad,
                color: '#000',
                fillColor: fill,
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            });
        }
    });
    waypoint_displays.addTo(map);

    for (var i = 0; i<wayline_data.length; i++) {
        if (drawn_once) {
            try {
                map.removeLayer(wayline_displays[i]);
            } catch (err) {
            }
        }
        wayline_displays[i] = L.polyline(wayline_data[i], wayline_styles[i]);
        wayline_displays[i].addTo(map);
    }

    drawn_once = true;
}
