// File to manage the global variables and functions

$('#logoutButton').click(function() {
    localStorage.removeItem('token');
    window.location.href = '/user/signin/';
});

$(document).ready(function() {
    // First check if the user is logged in. If not, redirect to the login page

    // Hack for now:
    //  check if your url is not base/user/signin/ or base/user/signup/
    //  if anything has user in it, then dont redirect it

    // Get the current URL
    var url = window.location.href;

    // Check if the URL contains "user" in it
    if (url.includes("user")) {
        // Do nothing for now
    } else {
        // Check if localStorage.getItem("token") exists
        // If it does not exist, redirect to the login page
        if (localStorage.getItem("token") === null) {
            window.location.href = "/user/signin/";
        }

        // So if it is valid then we can make the ajax call
        // Get the user's details
        $.ajax({
            url: window.location.origin + '/user/details/',
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("token")}`,
                'content-type': 'application/json'
            },
            type: 'get',
            success: function (response) {
                $('#userNameDisplay').text(response.user_details.user.first_name + " " + response.user_details.user.last_name);
            },
            error: function (response) {
                console.log(response);
            }
        });
    }

});