var event_id = window.location.href.split('/event/')[1];

function submitCancel(cancel_url, price) {
    var message_id = '#message';
    $(message_id).show();
    $.ajax({
        type: 'POST',
        url: cancel_url,
        dataType: 'JSON',
        data: {'price': price}
    }).done(function(data){
        if (data['success']) {
            $(message_id).text('Cancel sent. Please wait a moment for it to take effect...');
        } else if (data['error']) {
            $(message_id).text(data["error"]);
        }
    })
}

function submitTrade(trade_url, side) {
    var button_id = '#' + side+ '_button'
    var price_id = "#" + side + "_price";
    var qty_id = "#" + side + "_qty";
    var message_id = '#message';
    var qty = $(qty_id).val();
    var price = $(price_id).val();
    $(message_id).show();
    $.ajax({
        type: 'POST',
        url: trade_url,
        dataType: 'JSON',
        data: {'qty': qty, 'side': side, 'price': price}
    }).done(function(data){
        console.log(data);
        if (data['success']) {
            $(message_id).text('Order Sent. Please wait a moment for it to take effect...');
        } else if (data['error']) {
            $(message_id).text(data["error"]);
            $(price_id).val("");
            $(qty_id).val("");
            $(button_id).show();
        }
    })
}

/*
function pretty_print(d){
    d = String(d);
    var splitsies = d.split('.');
    if (splitsies.length == 1){
        return splitsies[0] + '.00';
    }
    else if (splitsies[1].length == 1){
        return splitsies[0] + '.' + splitsies[1] + '0';
    }
    else{
        return splitsies[0] + '.' + splitsies[1].substring(0,2);
    }
}

$(function(){
    $("#num_shares_yes").keyup(function(){
        var n = $("#num_shares_yes").val();

        if (/^\s*$/.test(n)){
            $("#total_price_yes").text('');
        }

        else if (isNaN(n)){
            $("#total_price_yes").text('');
        }

        else {
            n = parseInt(n);
            var price = $("#price_yes").text();
            price = parseFloat(price);
            $("#total_price_yes").text('Approximate price: ' + pretty_print(n * price));
        }
    })

    $("#num_shares_no").keyup(function() {
        var n = $("#num_shares_no").val();

        if (/^\s*$/.test(n)){
            $("#total_price_no").text('');
        }

        else if (isNaN(n)){
            $("#total_price_no").text('');
        }

        else {
            n = parseInt(n);
            var price = $("#price_no").text();
            price = parseFloat(price);
            $("#total_price_no").text('Approximate price: ' + pretty_print(n * price));
        }


    })
})
*/
