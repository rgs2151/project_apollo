// Utility function to make columns for DataTables
function make_columns(data) {
    return Object.keys(data[0]).map(key => {
        return { "data": key, "title": key.charAt(0).toUpperCase() + key.slice(1) };
    });
}

$(document).ready(function() {
    // Fetch the goals
    $.ajax({
        url: window.location.origin + '/conversation/user-goals/',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function(response) {
            console.log(response);

            if (response.data.length != 0) {
                // Make the DataTable
                $('#allGoals').DataTable(
                    {
                        data: response.data,
                        columns: make_columns(response.data),
                    }
                );
            
            } else {
                $('#allGoals').text('No goal record found');
            }
        },
        error: function(error) {
            console.log(error);
        }   
    });
});