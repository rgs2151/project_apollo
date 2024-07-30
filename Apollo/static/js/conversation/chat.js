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

    // Document upload button connected to input:
    $('#uploadDocumentButton').click(function() {
        $('#fileInput').click();
    });
});


// Submit the user's response to the assistant
$("#submitResponseButton").click(function () {
    var prompt = $("#responseInput").val();
    
    console.log(prompt);

    // disable the button
    $("#submitResponseButton").prop('disabled', true);


    $.ajax({
        url: window.location.origin + '/conversation/converse/',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'post',
        data: JSON.stringify({ 
            'message': {
                "role": "user",
                "content": prompt
            }, 
        }),
        success: function (response) {
            console.log(response);
            $("#assistantResponseDisplay").text(response.message.content);
            $("#convModeDisplay").text(response.conversation_state);
            
            // enable the button
            $("#submitResponseButton").prop('disabled', false);
        },
        error: function (response) {
            console.log(response);
            $("#assistantResponseDisplay").text("error in response");

            // enable the button
            $("#submitResponseButton").prop('disabled', false);
        }
    });

    $("#responseInput").val('');
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

// Upload the document!

// $('#fileInput').change(function(event) {
//     var file = event.target.files[0];
//     if (file) {

//         $("#uploadDocumentButton").prop('disabled', true);

//         // Process the file here
//         console.log('File selected:', file.name);
//         var formData = new FormData();
//         formData.append('file', file);
//         formData.append('file_type', "pdf");
        
//         $.ajax({
//             url: window.location.origin + '/conversation/documents/',
//             headers: {'Content-Type': 'application/json'},
//             xhrFields: { withCredentials: true },
//             type: 'post',
//             data: formData,
//             processData: false,
//             contentType: false,
//             success: function (response) {
//                 console.log(response);
//                 $("#uploadDocumentButton").prop('disabled', false);
//             },
//             error: function (response) {
//                 console.log(response);
//                 $("#uploadDocumentButton").prop('disabled', false);
//             }
//         });
//     }
// });

$('#fileInput').change(function(event) {
    var file = event.target.files[0];
    if (file) {

        $("#uploadDocumentButton").prop('disabled', true);

        // Process the file here
        console.log('File selected:', file.name);
        var reader = new FileReader();

        reader.onload = function(e) {
            var base64String = e.target.result.split(',')[1];
            console.log(typeof base64String);
            var data = {
                file: base64String,
                file_type: "pdf"
            };

            $.ajax({
                url: window.location.origin + '/conversation/documents/',
                headers: {'Content-Type': 'application/json'},
                xhrFields: { withCredentials: true },
                type: 'post',
                data: JSON.stringify(data),
                success: function (response) {
                    console.log(response);
                    $("#uploadDocumentButton").prop('disabled', false);
                },
                error: function (response) {
                    console.log(response);
                    $("#uploadDocumentButton").prop('disabled', false);
                }
            });
        };

        reader.readAsDataURL(file);
    }
});
