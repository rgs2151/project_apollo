// Utility function to make columns for DataTables
function make_columns(data) {
    return Object.keys(data[0]).map(key => {
        return { "data": key, "title": key.charAt(0).toUpperCase() + key.slice(1) };
    });
}

// For every row in the appointment_requests array, add 2 key-value pairs called 'Accept' and 'Reject'
function add_buttons(data) {
    return data.forEach(function(row) {
        row['Accept'] = '<button class="btn btn-success btn-circle btn-sm accept-button"><i class="fas fa-check"></i></button>';
        row['Reject'] = '<button class="btn btn-danger btn-circle btn-sm reject-button"><i class="fas fa-trash"></i></button>';
    });
};

function accept_and_reject_events(context, state) {
    let data = $('#appointmentRequests').DataTable().row($(context).parents('tr')).data();
    $.ajax({
        url: window.location.origin + '/conversation/doctor-events/',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'put',
        data: JSON.stringify({ 'id': data.id, 'event_status': state}),
    });
    $('#appointmentRequests').DataTable().row($(context).parents('tr')).remove().draw();
}

function make_appointment_request_entry(appointment){
    return `
            <div class="card d-flex flex-column p-2">
                <h5 class="card-title">${appointment.session.user_details.user.first_name} ${appointment.session.user_details.user.last_name}</h5>
                <div class="d-flex flex-row justify-content-between">
                    <p class="card-text"><i class="fas fa-envelope"></i> ${appointment.session.user_details.user.email}</p>
                    <p class="card-text"><i class="fas fa-calendar-alt"></i> ${appointment.event_date}</p>
                    <p class="card-text"><i class="fas fa-clock"></i> ${appointment.event_time}</p>
                    <button class="btn btn-success btn-circle btn-sm accept-button" data-event_id=${appointment.id}><i class="fas fa-check"></i></button>
                    <button class="btn btn-danger btn-circle btn-sm reject-button" data-event_id=${appointment.id}><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;

}

$(document).ready(function() {
    // Fetch the appointment requests
    $.ajax({
        // url: window.location.origin + '/conversation/doctor-events-dashboard/',
        url: window.location.origin + '/conversation/doctor-events-dashboard/?event_status=false',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function(response) {
            console.log(response);

            if (response.data.length === 0) {
                $('#appointmentRequests').text('No appointment requests found');
                return;
            }

            let table_data = response.data;
            
            add_buttons(table_data);

            // Make the DataTable
            $('#appointmentRequests').DataTable(
                {
                    data: table_data,
                    columns: make_columns(table_data),
                }
            );

            // Hide some columns
            $('#appointmentRequests').DataTable().columns([0,4,5]).visible(false);
    
            $('#appointmentRequests').DataTable().on('click', '.accept-button', function() {accept_and_reject_events(this, true);});
        
            $('#appointmentRequests').DataTable().on('click', '.reject-button', function() {accept_and_reject_events(this, false);});

            // response.data.forEach(appointment => {
            //     $('#dr_appointment_requests').append(make_appointment_request_entry(appointment));
            // });

            // $('#dr_appointment_requests').on('click', '.accept-button', function() {
            //     let event_id = $(this).data('event_id');
            //     $.ajax({
            //         url: window.location.origin + '/conversation/doctor-events/',
            //         headers: {'Content-Type': 'application/json'},
            //         xhrFields: { withCredentials: true },
            //         type: 'put',
            //         data: JSON.stringify({ 'id': event_id, 'event_status': true}),
            //         success: function(response) {
            //             console.log(response);
            //             $(this).parents('.card').remove();
            //         },
            //         error: function(error) {
            //             console.log(error);
            //         }
            //     });
            // });

            // $('#dr_appointment_requests').on('click', '.reject-button', function() {
            //     let event_id = $(this).data('event_id');
            //     $.ajax({
            //         url: window.location.origin + '/conversation/doctor-events/',
            //         headers: {'Content-Type': 'application/json'},
            //         xhrFields: { withCredentials: true },
            //         type: 'put',
            //         data: JSON.stringify({ 'id': event_id, 'event_status': false}),
            //         success: function(response) {
            //             console.log(response);
            //             $(this).parents('.card').remove();
            //         },
            //         error: function(error) {
            //             console.log(error);
            //         }
            //     });
            // });

        },
        error: function(error) {
            console.log(error);
        }   
    });
});