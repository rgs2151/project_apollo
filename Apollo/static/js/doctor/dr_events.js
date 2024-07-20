// Utility function to make columns for DataTables
function make_columns(data) {
    return Object.keys(data[0]).map(key => {
        return { "data": key, "title": key.charAt(0).toUpperCase() + key.slice(1) };
    });
}

$(document).ready(function () {
    $.ajax({
        url: window.location.origin + '/conversation/doctor-events-dashboard/',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function(response) {
            console.log(response);

            if (response.data.length === 0) {
                $('#allAppointments').text('No appointment record found');
                return null;
            }
        
            // Make the DataTable
            $('#allAppointments').DataTable(
                {
                    data: response.data,
                    columns: make_columns(response.data),
                }
            );
        },
        error: function(error) {
            console.log(error);
            return null;
        }   
    });

});