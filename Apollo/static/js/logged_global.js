// Util funtions:

// File to manage the global variables and functions
$(document).ready(function() {
    $('#logoutButton').click(function() {
        $.ajax({
            url: window.location.origin + '/user/logout/',
            headers: {'content-type': 'application/json'},
            xhrFields: { withCredentials: true },
            type: 'post',
            success: function (response) {
                window.location.href = '/user/signin/';
            },
            error: function (response) {
                console.log(response);
            }
        });
    });
});