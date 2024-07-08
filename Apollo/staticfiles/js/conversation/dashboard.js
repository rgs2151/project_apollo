// Dashboard Javascrips

// Utility function to make columns for DataTables
function make_columns(data) {
    return Object.keys(data[0]).map(key => {
        return { "data": key, "title": key.charAt(0).toUpperCase() + key.slice(1) };
    });
}

// Health Indicators
var healthIndicatorsData = [
    {
        "name":       "Tiger Nixon",
        "position":   "System Architect",
        "salary":     "$3,120",
        "start_date": "2011/04/25",
        "office":     "Edinburgh",
        "extn":       "5421"
    },
    {
        "name":       "Garrett Winters",
        "position":   "Director",
        "salary":     "$5,300",
        "start_date": "2011/07/25",
        "office":     "Edinburgh",
        "extn":       "8422"
    }
]

// Upcoming Events
var upcomingEventsData = [
    {
        "date": "2011/04/25",
        "event": "Event 1",
        "location": "Hospital A",
    },
    {
        "date": "2011/07/25",
        "event": "Event 2",
        "location": "Hospital A",
    }
]

// Make the DataTables
$(document).ready(function() {
    $('#healthIndicators').DataTable(
        {
            data: healthIndicatorsData,
            columns: make_columns(healthIndicatorsData)
        }
    );

    $('#upcomingEvents').DataTable(
        {
            data: upcomingEventsData,
            columns: make_columns(upcomingEventsData),
            searching: false,
        }
    );
});
