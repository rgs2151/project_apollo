// @request_schema_validation(schema={
//     "first_name": {"type": "string", "required": False, "empty": False, "nullable": True, "minlength": 3, "maxlength": 20},
//     "last_name": {"type": "string", "required": False, "empty": False, "nullable": True, "minlength": 1, "maxlength": 20},
//     "email": {"type": "string", "required": True, "empty": False, "nullable": True, "minlength": 5, "maxlength": 75, "check_with": "email"},
//     "password": {"type": "string", "required": True, "empty": False, "nullable": False, "minlength": 8, "maxlength": 36, "check_with": "password"},
// })

function validate_data(first_name, last_name, email, password, confirm_password) {
    // Validate data and alert the user
    if (first_name.length < 3 || first_name.length > 20) {
        alert('First name must be between 3 and 20 characters');
        return false;
    }
    if (last_name.length < 1 || last_name.length > 20) {
        alert('Last name must be between 1 and 20 characters');
        return false;
    }
    if (email.length < 5 || email.length > 75) {
        alert('Email must be between 5 and 75 characters');
        return false;
    }
    if (password.length < 8 || password.length > 36) {
        alert('Password must be between 8 and 36 characters');
        return false;
    }
    if (password != confirm_password) {
        alert('Passwords do not match');
        return false;
    }
    return true;
}


$('#registerButton').click(function() {
    // Get the data from the form
    var first_name = $('#FirstName').val();
    var last_name = $('#LastName').val();
    var email = $('#InputEmail').val();
    var password = $('#InputPassword').val();
    var confirm_password = $('#RepeatPassword').val();
    // Validate the data
    if (!validate_data(first_name, last_name, email, password, confirm_password)) {
        return;
    }
    // Send the data to the server
    $.ajax({
        url: window.location.origin + '/user/register/',
        headers: {'content-type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'post',
        data: JSON.stringify({
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password
        }),
        success: function (response) {
            window.location.href = '/user/signin/';
        },
        error: function (response) {
            console.log(response);
            alert('An error occurred while registering');
        }
    });
});