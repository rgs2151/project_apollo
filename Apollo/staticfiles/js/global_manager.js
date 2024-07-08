// File to manage the global variables and functions

$(document).ready(function() {
    // First check if the user is logged in. If not, redirect to the login page

    // Hack for now:
    //  check if your url is not base/user/signin/ or base/user/signup/
    //  if anything has user in it, then dont redirect it

    // Get the current URL
    var url = window.location.href;

    // Check if the URL contains "user" in it
    if (url.includes("user") === false) {
        // Check if localStorage.getItem("token") exists
        // If it does not exist, redirect to the login page
        if (localStorage.getItem("token") === null) {
            window.location.href = "/user/signin/";
        }
    }

});