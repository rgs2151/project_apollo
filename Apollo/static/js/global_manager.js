// File to manage the global variables and functions

$(document).ready(function() {
    // First check if the user is logged in. If not, redirect to the login page

    // Check if localStorage.getItem("token") exists
    // If it does not exist, redirect to the login page
    if (localStorage.getItem("token") === null) {
        window.location.href = "/user/signin/";
    }
});