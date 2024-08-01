// ================================= //
// Setups//
// ================================= //

// Document upload button connected to input:
$('#uploadImageButton').click(function() {
    $('#fileInput').click();
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

// Use the microphone
var currently_speaking = false;
$("#microphoneButton").click(function () {
    if (currently_speaking) {
        $(this).css('color', 'white');
        currently_speaking = false;
        
        // set a 2s timeout to stop the microphone
        setTimeout(function() {
            annyang.pause();
        }, 3000);
        
        console.log('Stopped Listening...');
    } else {
        $(this).css('color', 'red');
        currently_speaking = true;
        
        annyang.resume();

        console.log('Listening...');
    }
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

let temp_image_holder = null;


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
            
            current_state = null;
            
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
                    make_user_response(text, sess_state);
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
    }
});

// Submit the user's response to the assistant
$("#submitResponseButton").click(function () {
    var prompt = $("#responseInput").val();

    // disable the button
    $("#submitResponseButton").prop('disabled', true);
    
    make_user_response(prompt, "normal", temp_image_holder);

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
            console.log(response.conversation_state);

            make_assistant_response(
                response.message.content, 
                "normal"
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

