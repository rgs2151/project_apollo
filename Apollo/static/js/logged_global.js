// File to manage the global variables and functions

$(document).ready(function() {
    // So if it is valid then we can make the ajax call
    // Get the user's details
    // $.ajax({
    //     url: window.location.origin + '/user/details/',
    //     headers: {
    //         'content-type': 'application/json'
    //     },
    //     xhrFields: { withCredentials: true },
    //     type: 'get',
    //     success: function (response) {
    //         $('#userNameDisplay').text(response.user_details.user.first_name + " " + response.user_details.user.last_name);
    //     },
    //     error: function (response) {
    //         console.log(response);
    //     }
    // });

    
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