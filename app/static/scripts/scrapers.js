/**
 * Created by ryanrushton on 23/08/2016.
 */

function get_vals () {
    $.getJSON("/_get_pastebin_scraper_stats",
        function (data){
            var ps_is_alive = data.ps_is_alive.toString()
            ps_is_alive = ps_is_alive.charAt(0).toUpperCase() + ps_is_alive.slice(1)
            $('#ps_is_alive').text(ps_is_alive)
            $('#ps_last_response_address').text(data.ps_last_response_address)
            document.getElementById("ps_last_response_address").href = data.ps_last_response_address
            $('#ps_last_response_code').text(data.ps_last_response_code)
            var ps_using_tor = data.ps_using_tor.toString()
            ps_using_tor = ps_using_tor.charAt(0).toUpperCase() + ps_using_tor.slice(1)
            $('#ps_using_tor').text(ps_using_tor)
        });
}
setTimeout('get_vals()', 10);
setInterval('get_vals()', 500);