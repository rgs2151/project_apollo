// Dashboard Javascrips

// Utility function to make columns for DataTables
function make_columns(data) {
    return Object.keys(data[0]).map(key => {
        return { "data": key, "title": key.charAt(0).toUpperCase() + key.slice(1) };
    });
}

function make_goal_entry(goal) {
    return `
        <h4 class="small font-weight-bold">${goal.goal_description} <span class="float-right">${goal.goal_progress}%</span></h4>
        <div class="progress mb-4">
            <div class="progress-bar bg-danger" role="progressbar" style="width: ${goal.goal_progress}%" aria-valuenow="${goal.goal_progress}" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
    `;
}

function make_event_entry(event){
    return `
        <div class="card mb-4 p-2">
            <div class="d-flex justify-content-between">
                <h5 class="card-title">${event.event_description}</h5>
            </div>
            <div class="d-flex justify-content-between">
                <p class="card-text"><i class="fas fa-user-md"></i> ${event.event_contact}</p>
                <p class="card-text"><i class="fas fa-calendar-alt"></i> ${event.event_date}</p>
                <p class="card-text"><i class="fas fa-clock"></i> ${event.event_time}</p>
                <div class="d-flex" style="position: relative; top: -20px;">

                    ${event.event_status ? 
                        `<a href="${window.location.origin + '/conversation/confirmed-events/' + event.id}" target="_blank" class="btn btn-primary"><i class="fas fa-door-open"></i> Appointment Page</a>` :
                        `<button class="btn btn-secondary" disabled><i class="fas fa-clock"></i> Pending Approval</button>`
                    }

                </div>
            </div>
        </div>
    `;
}

$(document).ready(function() {

    // Populate the health indicators table
    $.ajax({
        url: window.location.origin + '/conversation/history/',
        headers: {'content-type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'post',
        data: JSON.stringify({ 'type': 'history'}),
        success: function (response) {
            console.log(response);

            if (response.data.length === 0) {
                $('#healthIndicators').text("No history found");
                return;
            }

            // Make the DataTable
            $('#healthIndicators').DataTable(
                {
                    data: response.data,
                    columns: make_columns(response.data),
                }
            );

            $('#healthIndicators').DataTable().columns([0,1,5, 6]).visible(false);

        },
        error: function (response) {
            console.log(response);
        }
    });

    // Populate the upcoming events table
    $.ajax({
        url: window.location.origin + '/conversation/user-events-dashboard/',
        headers: {'content-type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function (response) {
            console.log(response);

            if (response.data.length === 0) {
                $('#upcomingEvents').text("No upcoming events found");
                return;
            }
            response.data.forEach(event => {
                $('#upcomingEvents').append(make_event_entry(event));
            });
        },
    });

    // Populate the goals and milestones section
    $.ajax({
        url: window.location.origin + '/conversation/user-goals/',
        headers: {'content-type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'get',
        success: function (response) {
            console.log(response.data);

            if (response.data.length === 0) {
                $('#goalHolder').text("No goals found");
                return;
            }

            response.data.forEach(goal => {
                $('#goalHolder').append(make_goal_entry(goal));
            });

        },
        error: function (response) {
            console.log(response);
        }
    });
});