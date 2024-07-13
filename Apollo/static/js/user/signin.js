
$('#loginButton').click(function() {
    var username = $('#InputEmail').val();
    var password = $('#InputPassword').val();
    $.ajax({
        type: 'POST',
        Headers: {
            'content-type': 'application/json'
        },
        url: '/user/login/',
        data: {
            email: username,
            password: password,
        },
        success: function(data) {
            // localStorage.setItem('token', data.auth_token);
            window.location.href = '/conversation/dashboard/';
        },
        error: function(data) {
            alert('Invalid Credentials');
        }
    });
});