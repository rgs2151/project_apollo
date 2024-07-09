

// Submit the user's response to the assistant
$("#submitResponseButton").click(function () {
    var prompt = $("#responseInput").val();
    
    console.log(prompt);

    // disable the button
    $("#submitResponseButton").prop('disabled', true);


    $.ajax({
        url: window.location.origin + '/conversation/converse/',
        headers: {"Authorization": `Bearer ${localStorage.getItem("token")}`, 'Content-Type': 'application/json'},
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
            $("convModeDisplay").text(response.conversation_state);
            
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


// Upload the document!

