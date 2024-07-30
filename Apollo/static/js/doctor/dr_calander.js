$(document).ready(function () {

    let calendar = new EventCalendar(document.getElementById('calendarHolder'), {
        view: 'timeGridWeek',
    });

    // Fetch the appointment requests
    $.ajax({
        url: window.location.origin + '/conversation/doctor-events-dashboard/?event_status=true',
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function(response) {
            console.log(response);

            response.data.forEach(function(event) {
                // event.event_date // YYYY-MM-DD
                // event.event_time // HH:MM:SS
                // event.id // event id

                // Convert to date object and add 2 hrs
                let start = new Date(event.event_date + 'T' + event.event_time);
                let end = new Date(event.event_date + 'T' + event.event_time);
                end.setHours(end.getHours() + 2);

                calendar.addEvent({
                    title: 'User id: ' + event.user_id + ' \nEvent id: ' + event.id,
                    start: start,
                    end: end,
                    color: '#191919',
                });
            });
        },
        error: function(error) {
            console.log(error);
        }
    });
});