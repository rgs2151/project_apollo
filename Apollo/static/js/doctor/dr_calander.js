$(document).ready(function () {

    let calendar = new EventCalendar(document.getElementById('calendarHolder'), {
        view: 'timeGridWeek',
        height: '55vh',
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
                    title: 'Title: ' + event.event_description,
                    start: start,
                    end: end,
                    color: '#191919',
                    extendedProps: {
                        'complete_event': event,
                    }
                });
            });
        },
        error: function(error) {
            console.log(error);
        }
    });

    calendar.setOption('eventClick', function eventClick(info) {
        // console.log(info.event.extendedProps.complete_event);
        href = window.location.origin + '/conversation/confirmed-events/' + info.event.extendedProps.complete_event.id;
        window.open(href, '_blank');
    });
});