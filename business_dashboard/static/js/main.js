// This is file contains the main js control logic.

// Global context variables
var max_business_display_num = 20000;
var route_speed_thresh = 'none';
var business_bounds = [37.36, -122.16, 37.43, -122.02];
var mode = 'startup';
var boundary_type = 'none';
var boundary_side = 'none';
var sub_mode = 'none';
var ref_lat = 'none';
var ref_lng = 'none';
var reachable_polygons = [];
var reachable_points = [];
var reachable_latlngs = [];
var disp_route = [];
var route_latlngs = [];
var is_busy = false;

var selected_ind = -1;
var all_button_names = ['#route_button', '#sim_popout_button', '#reachable_button'];
var last_zoom = 0;
var drawn_once = false;

var map_start_latlng = [37.37901, -122.07188];
var map = L.map('map_div').setView(map_start_latlng, 14);

var background_layer = Tangram.leafletLayer({
   scene: '/static/osm.yaml',
});
background_layer.addTo(map);

function load_background(bg_name) {
    map.removeLayer(background_layer);
    background_layer = Tangram.leafletLayer({
       scene: '/static/' + bg_name + '.yaml'
    });
    background_layer.addTo(map);
}

function gray_all_buttons() {
    for (var i = 0; i<all_button_names.length; i++) {
        var other = all_button_names[i];
        $(other).removeClass('btn btn-primary');
        $(other).addClass('btn btn-default');
    }
}

function update_status(input_text) {
    var text = '';
    if (input_text) {
        text = input_text;
        $('#status').text(' ' + text + ' ');
    } else {
        if (mode == 'reachable_region') {
            text = 'click businesses, and then press "q" to compute reachable regions';
        } else {
            text = 'should be self-explanatory. If not, ask Jeff.';
        }
        $('#status').text(' Help: ' + text + ' ');
    }
}

function loading_status() {
    $('#status').text(' Please wait... ');
    is_busy = true;
}

function on_click(e) {
    if (is_busy) {
        return;
    }
    var window_width = $(window).width();
    if (e.pageX > window_width*0.9 || e.pageX < window_width * 0.05) {
        return;
    }

    var new_xy = [e.pageX, e.pageY];
    var latlng = map.containerPointToLatLng(new_xy);
    latlng = [latlng.lat, latlng.lng];
    console.log(latlng);
    if (mode == 'route') {
        if (route_latlngs.length == 2) {
            route_latlngs = [];
            disp_route = [];
        }

        if (route_latlngs.length == 0) {
            route_latlngs.push(latlng);
            draw();
        } else {
            route_latlngs.push(latlng);
            finish_find_route();
        }
    } else if (mode == 'reachable_region') {
        if (stale_polygons) {
            stale_polygons = false;
            reachable_polygons = [];
            reachable_points = [];
            reachable_latlngs = [];
        }

        reachable_latlngs.push(latlng);
        draw();
    }

}

// Handle keypresses
$(window).keypress(function(e) {
    var key = e.which;
    if (key == 113) { // q
        if (mode == 'reachable_region') finish_reachable_region();
    }
});

// Distinguish between clicking and dragging
var flag = 0;
last_x = 0;
last_y = 1;

var click_thing = document;
$(click_thing).mousedown(function(e){
    last_x = e.screenX;
    last_y = e.screenY;
    flag = 0;
});
$(click_thing).mousemove(function(e){
    flag = 1;
});
$(click_thing).mouseup(function(e){
    var dx = e.screenX - last_x;
    var dy = e.screenY - last_y;
    if (flag==1 && dx*dx + dy*dy > 100){
        return;
    } else {
        on_click(e);
    }
});
draw();
