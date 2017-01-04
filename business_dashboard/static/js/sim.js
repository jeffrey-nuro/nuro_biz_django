// This file contains the js functionality related to running simulations.

$('#sim_input_popover').popover({
    html: true,
    placement: 'left',
    title: $('#sim_input_title').html(),
    content: $('#sim_input_table').html().split('id="').join('id="real_'),
});

$('#sim_results_popover').popover({
    html: true,
    placement: 'left',
    title: $('#sim_results_title').html(),
    content: function () { return $('#sim_results_table').html(); }
});

function submit_sim() {
    if (is_busy) {
        return;
    }

    sim_params = {
        'num_robots': parseInt($('#real_sim_num_robots').val()),
        'business_prep_time_min': parseFloat($('#real_sim_business_prep').val()),
        'customer_pickup_time_min': parseFloat($('#real_sim_customer_pickup').val()),
        'num_requests': parseInt($('#real_sim_num_requests').val()),
        'business_radius_mi': parseFloat($('#real_sim_business_radius').val()),
        'robot_max_speed_mph': parseFloat($('#real_sim_robot_max_speed').val()),
        'road_speed_thresh_mph': parseFloat($('#real_sim_road_max_speed').val()),
        'traffic_multiplier': parseFloat($('#real_sim_traffic_multiplier').val()),
    };

    for (var i in sim_params) {
        if (isNaN(sim_params[i])) {
            alert('Please make sure that ' + i + ' is a number');
            return;
        }
    }

    sim_params.robot_start = 'random';
    sim_params.mode = 'sim';

    $.ajax({
        type: 'POST',
        url: '/',
        data: sim_params,
        dataType: 'JSON',
    }).done(function(data) {
        $('#sim_input_popover').popover('hide');
        $('#sim_res_wait_time').html(data.wait_time);
        $('#sim_res_pickup_time').html(data.pickup_time);
        $('#sim_res_delivery_time').html(data.dropoff_time);
        $('#sim_res_best_case_time').html(data.required_time);
        $('#sim_res_service_ratio').html(data.service_ratio);
        $('#sim_results_popover').popover('show');
        update_status('Simulation done, see "Sim results" for metrics.');
        is_busy = false;
    });

    is_busy = true;
    async function status_bar() {
        var requests_per_second = 2;
        for (var i = 0; i < 100; ++i) {
            if (!is_busy) {
                update_status('Simulation done, see "Sim results" for metrics.');
            } else {
                await sleep(sim_params.num_requests / requests_per_second * 9);
                update_status('Simulation approx. progress: ' + i + '%, please wait.');
            }
        }
    }

    status_bar();
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
