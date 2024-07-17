// Dashboard Javascrips

// Utility function to make columns for DataTables
function make_columns(data) {
    return Object.keys(data[0]).map(key => {
        return { "data": key, "title": key.charAt(0).toUpperCase() + key.slice(1) };
    });
}



$(document).ready(function() {
    $.ajax({
        url: window.location.origin + '/conversation/history/',
        headers: {'content-type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'post',
        data: JSON.stringify({ 'type': 'history'}),
        success: function (response) {
            console.log(response);

            if (response.data.length === 0) {
                $('#healthIndicators').text("No history found");
                return;
            }

            // Make the DataTable
            $('#healthIndicators').DataTable(
                {
                    data: response.data,
                    columns: make_columns(response.data),
                }
            );

            $('#healthIndicators').DataTable().columns([0,1]).visible(false);

        },
        error: function (response) {
            console.log(response);
        }
    });

    $.ajax({
        url: window.location.origin + '/conversation/events/',
        headers: {'content-type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function (response) {
            console.log(response);

            if (response.data.length === 0) {
                $('#upcomingEvents').text("No upcoming events found");
                return;
            }

            // Make the DataTable
            $('#upcomingEvents').DataTable(
                {
                    data: response.data,
                    columns: make_columns(response.data),
                    searching: false,
                }
            );

            $('#upcomingEvents').DataTable().columns([0,1,2,6]).visible(false);

        },
    });
});