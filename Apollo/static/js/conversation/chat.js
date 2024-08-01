// ================================= //
// Setups//
// ================================= //

// Document upload button connected to input:
$('#uploadImageButton').click(function() {
    $('#fileInput').click();
});

$('#resetStateButton').click(function() {
    reset_state();
});

// make it such that when user press enter while typing the response, it submits the response
$("#responseInput").keypress(function (e) {
    if (e.which == 13) {
        $("#submitResponseButton").click();
    }
});

$("#closeImageButton").click(function() {
    $("#imgUploadHolder").css('display', 'none');
    $("#imageHolder").attr('src', '');
    $("#fileInput").val('');
    temp_image_holder = null;

    $("#uploadImageButton").prop('disabled', false);
});


// ================================= //
// Voice Recognition Section//
// ================================= //

// As the document loads, setup things
$(document).ready(function () {
    // Setup the voice recognition
    if (annyang) {
        annyang.start({ autoRestart: true, continuous: true, paused: true });
        // Start listening.
        annyang.addCallback('result', function (phrases) {
            
            var total_prompt = $("#responseInput").val();
            total_prompt += phrases[0] + ' ';
            console.log('I think the user said: ', phrases[0]);
            $("#responseInput").val(total_prompt);
        });
    
    } else {
        console.log('Annyang not available');
    }
});

// make it such that the microphone is push to talk instead by holding the button, when the button is released, it stops listening
$("#microphoneButton").mousedown(function () {
    annyang.resume();
    
    console.log('Listening...');
    $(this).css('color', 'red');
});

$("#microphoneButton").mouseup(function () {

    $(this).css('color', 'white');

    // disable the microphone button and set it to loading rotation
    $(this).prop('disabled', true);
    // get its child i element and set its class to fa spin
    // remove the microphone icon first
    $(this).children('i').removeClass('fa-microphone');
    $(this).children('i').addClass('fa-spinner loader');
    // $(this).children('i').addClass('');
    
    setTimeout(function() {
        annyang.pause();
        // enable the microphone button and set it to normal
        $('#microphoneButton').prop('disabled', false);
        $('#microphoneButton').children('i').removeClass('fa-spinner loader');
        $('#microphoneButton').children('i').addClass('fa-microphone');
    }, 2500);

    console.log('Stopped Listening...');
});


// ================================= //
// Cat Section//
// ================================= //

// helper functions
function make_assistant_response(response_text, state) {
    // <div class="message-wrapper">
    //     <div class="message-assistant message-normal">Hi, I am your health assistant. How are you doing today?</div>
    // </div> 
    // make that div with jquery and append it to the chat_history_area div
    var message_wrapper = $('<div class="message-wrapper"></div>');
    var message = $('<div class="message-assistant message-'+ state +'"></div>');
    message.text(response_text);
    message_wrapper.append(message);

    $("#chat_history_area").prepend(message_wrapper);
}

function make_user_response(response_text, state, image_url = null) {
    // <div class="message-wrapper">
    //     <img src="https://images.template.net/wp-content/uploads/2017/06/Medical-Emergency-Incident-Report.jpg">
    //     <div class="message-user message-normal">Yes here is an image</div>
    // </div>
    var message_wrapper = $('<div class="message-wrapper"></div>');
    if (image_url) {
        var image = $('<img src="'+ image_url +'">');
        message_wrapper.append(image);
    }
    var message = $('<div class="message-user message-'+ state +'"></div>');
    message.text(response_text);
    message_wrapper.append(message);

    $("#chat_history_area").prepend(message_wrapper);
}

function make_divider(state) {
    // <div class="divider divider-normal">
    //     <span>normal</span>
    // </div>
    var divider = $('<div class="divider divider-'+ state +'"></div>');
    var span = $('<span>'+ state +'</span>');
    divider.append(span);
    
    $("#chat_history_area").prepend(divider);
}

function reset_state() {
    // conversation/reset-chat-session/
    $.ajax({
        url: window.location.origin + '/conversation/reset-chat-session/',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'post',
        data: JSON.stringify({}),
        success: function(response) {
            console.log(response);

            current_state = "normal"; 

        },
        error: function(response) {
            console.log(response);
        }
    });
}

var temp_image_holder = null;
var current_state = null;


// Get the existing conversation
$(document).ready(function () {

    // conversation/chathistory/

    $.ajax({
        url: window.location.origin + '/conversation/chathistory/?page_size=100',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function (response) {
            console.log(response);
            // possible states: 'normal', 'goal', 'appointment_or_service', 'advice'
            
            for (var i = 0; i < response.data.length; i++) {
                var message = response.data[i];

                var text = message.prompt.content;
                var role = message.prompt.role;
                var sess_state = message.session.session_type.session_state.name;

                // clean the sess_state name:
                if (sess_state == "appointment_or_service_purchase") {
                    sess_state = "appointment";
                }

                // Make divider if the state has changed
                if (current_state != sess_state) {
                    make_divider(sess_state);
                    current_state = sess_state;
                }

                if (role == "user") {
                    // check if the content type is direct text has image
                    // if its a list then it has image assuming
                    if (typeof text === 'object') {
                        if (text[1]) {
                            // that means image is also there
                            make_user_response(text[0].text, sess_state, text[1].image_url.url);
                        } else {
                            // means one of the legacy one that just has text
                            // so we skip this for now hack
                            // make_user_response(text[0].text, sess_state);
                        }
                    } else {
                        make_user_response(text, sess_state);
                    }

                } else {
                    make_assistant_response(text, sess_state);
                }
            }
        },
        error: function (response) {
            console.log(response);
        }
    });

});


// Upload the document!
$('#fileInput').change(function(event) {
    var file = event.target.files[0];
    if (file) {

        $("#uploadImageButton").prop('disabled', true);

        // Process the file here
        console.log('File selected:', file.name);
        var reader = new FileReader();

        reader.onload = function(e) {
            var base64String = e.target.result.split(',')[1];
            temp_image_holder = "data:image/jpeg;base64,"+base64String;
        };

        reader.readAsDataURL(file);

        // enable the imageholder above the input field
        $("#imgUploadHolder").css('display', 'block');
        $("#imageHolder").attr('src', URL.createObjectURL(file));
    }
});

// Submit the user's response to the assistant
$("#submitResponseButton").click(function () {
    var prompt = $("#responseInput").val();

    // disable the button
    $("#submitResponseButton").prop('disabled', true);
    
    make_user_response(prompt, current_state, temp_image_holder);

    // make data to send to user
    if (temp_image_holder) {
        to_model = JSON.stringify({ 
            'message': {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": temp_image_holder}}
                ],
            }, 
        })

        // clear the image holder
        $('#closeImageButton').click();
    } else {
        to_model = JSON.stringify({ 
            'message': {
                "role": "user",
                "content": prompt
            }, 
        })
    }
    
    $.ajax({
        url: window.location.origin + '/conversation/converse/',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'post',
        data: to_model,
        success: function (response) {
            console.log(response);
            console.log(response.mode);

            new_state = response.mode
            // clean the sess_state name:
            if (new_state == "appointment_or_service_purchase") {
                new_state = "appointment";
            }

            // Make divider if the state has changed
            if (current_state != new_state) {
                make_divider(new_state);
                current_state = new_state;
            }

            make_assistant_response(
                response.message.content, 
                new_state
            );
            
            // enable the button
            $("#submitResponseButton").prop('disabled', false);
            $("#uploadImageButton").prop('disabled', false);
            temp_image_holder = null;
        },
        error: function (response) {
            console.log(response);

            // enable the button
            $("#submitResponseButton").prop('disabled', false);
            $("#uploadImageButton").prop('disabled', false);
            temp_image_holder = null;
        }
    });

    $("#responseInput").val('');
});

