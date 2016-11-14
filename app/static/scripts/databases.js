/**
 * Created by ryanrushton on 23/08/2016.
 */

function get_vals () {
    $.getJSON("/_get_database_dicts",
        function (data){
            $('#es_name').text(data.es_health_dict.cluster_name)
            $('#es_status').text(data.es_health_dict.status)
            $('#es_timed_out').text(data.es_health_dict.timed_out)
            $('#es_count').text(data.es_stats_dict.indices.docs.count)
            $('#es_deleted').text(data.es_stats_dict.indices.docs.deleted)
            $('#es_size').text(data.es_stats_dict.size)
            $('#es_available').text(data.es_stats_dict.available)
            $('#es_number_of_nodes').text(data.es_health_dict.number_of_nodes)
            $('#es_number_of_data_nodes').text(data.es_health_dict.number_of_data_nodes)
            $('#es_indices_count').text(data.es_stats_dict.indices.count)
            $('#es_shards_total').text(data.es_stats_dict.indices.shards.total)
            $('#es_shards_primaries').text(data.es_stats_dict.indices.shards.primaries)
            $('#es_active_shards').text(data.es_health_dict.active_shards)
            $('#es_active_primary_shards').text(data.es_health_dict.active_primary_shards)
            $('#es_initializing_shards').text(data.es_health_dict.initializing_shards)
            $('#es_relocating_shards').text(data.es_health_dict.relocating_shards)
            $('#es_unassigned_shards').text(data.es_health_dict.unassigned_shards)
            $('#es_delayed_unassigned_shards').text(data.es_health_dict.delayed_unassigned_shards)
            $('#es_active_shards_percent').text(data.es_health_dict.active_shards_percent_as_number)
            $('#postgres_name').text(data.postgres_dict.name)
            $('#postgres_tables').text(data.postgres_dict.tables)
            $('#postgres_paste_count').text(data.postgres_dict.paste)
        });
}
setTimeout('get_vals()', 10);
setInterval('get_vals()', 2000);