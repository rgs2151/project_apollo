$(document).ready(function () {

    let calendar = new EventCalendar(document.getElementById('calendarHolder'), {
        view: 'timeGridWeek',
    });

    calendar.addEvent({
        title: 'Event 1',
        start: '2024-07-20T10:00:00',
        end: '2024-07-20T12:00:00',
        color: 'teal',
    });
    calendar.addEvent({
        title: 'Event 2',
        start: '2024-07-19T09:00:00',
        end: '2024-07-19T11:00:00',
        color: 'teal',
    });
    calendar.addEvent({
        title: 'Event 3',
        start: '2024-07-19T14:00:00',
        end: '2024-07-19T16:00:00',
        color: 'teal',
    });

});