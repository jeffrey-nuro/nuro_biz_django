// This file contains the frontend for finding shortest paths and reachable polygons

function set_region_speed_threshold(thresh) {
    gray_all_buttons();
    route_speed_thresh = thresh;
    mode = 'reachable_region';
    route_latlngs = [];
    draw();
    $('#reachable_button').html('Region: ' + thresh + ' <span class="caret"></span>');
    $('#reachable_button').removeClass('btn btn-default');
    $('#reachable_button').addClass('btn btn-primary');
    update_status();
}

function set_route_speed_threshold(thresh) {
    gray_all_buttons();
    route_speed_thresh = thresh;
    mode = 'route';
    reachable_latlngs = [];
    draw();
    $('#route_button').html('Route: ' + thresh + ' and below <span class="caret"></span>');
    $('#route_button').removeClass('btn btn-default');
    $('#route_button').addClass('btn btn-primary');
}

function finish_reachable_region() {
    var minutes = $('#reachable_time_textarea').val();

    if (minutes.length == 0 || isNaN(minutes)) {
        alert('Please make sure the time threshold is a number');
        return;
    }
    var post_data = {'mode': mode, 'latlngs': JSON.stringify(reachable_latlngs),
        'radius': minutes*60, 'speed_thresh': route_speed_thresh};

    $.ajax({
        type: 'POST',
        url: 'reachable_region',
        data: post_data,
        dataType: 'JSON',
    }).done(function(data) {
        reachable_polygons = data.hull_arr;
        reachable_points = data.points_arr;
        draw();
        update_status();
        is_busy = false;
        stale_polygons = true;
    });
    loading_status();
}

function finish_find_route() {
    var post_data = {'mode': mode, 'route_latlngs': JSON.stringify(route_latlngs),
        'speed_thresh': route_speed_thresh,
        'traffic_multiplier': $('#traffic_multiplier_textarea').val()};
    $.ajax({
        type: 'POST',
        url: 'route',
        data: post_data,
        dataType: 'JSON',
    }).done(function(data) {
        disp_route = data.route;
        draw();
        if (disp_route.length == 0) {
            update_status('No route could be found.');
        } else {
            update_status('Shortest route is ' + data.dist.toString() + ' seconds.');
        }
    });
}
