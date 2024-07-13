// Utility function to make columns for DataTables
function make_columns(data) {
    return Object.keys(data[0]).map(key => {
        return { "data": key, "title": key.charAt(0).toUpperCase() + key.slice(1) };
    });
}

let appointment_requests = [
    {
        "id": 1,
        "patient": "John Doe",
        "date": "2020-12-12",
        "time": "12:00",
        "reason": "Headache",
        "status": "Pending",
    },
    {
        "id": 2,
        "patient": "Jane Doe",
        "date": "2020-12-13",
        "time": "13:00",
        "reason": "Fever",
        "status": "Pending",
    },
    {
        "id": 3,
        "patient": "John Smith",
        "date": "2020-12-14",
        "time": "14:00",
        "reason": "Cough",
        "status": "Pending",
    },
    {
        "id": 4,
        "patient": "Jane Smith",
        "date": "2020-12-15",
        "time": "15:00",
        "reason": "Sore Throat",
        "status": "Pending",
    },
    {
        "id": 5,
        "patient": "John Doe",
        "date": "2020-12-16",
        "time": "16:00",
        "reason": "Headache",
        "status": "Pending",
    },
    {
        "id": 6,
        "patient": "Jane Doe",
        "date": "2020-12-17",
        "time": "17:00",
        "reason": "Fever",
        "status": "Pending",
    },
    {
        "id": 7,
        "patient": "John Smith",
        "date": "2020-12-18",
        "time": "18:00",
        "reason": "Cough",
        "status": "Pending",
    },
    {
        "id": 8,
        "patient": "Jane Smith",
        "date": "2020-12-19",
        "time": "19:00",
        "reason": "Sore Throat",
        "status": "Pending",
    },
    {
        "id": 9,
        "patient": "John Doe",
        "date": "2020-12-20",
        "time": "20:00",
        "reason": "Headache",
        "status": "Pending",
    },
];

// For every row in the appointment_requests array, add 2 key-value pairs called 'Accept' and 'Reject'
function add_buttons(data) {
    return data.forEach(function(row) {
        row['Accept'] = '<button class="btn btn-success btn-circle btn-sm accept-button"><i class="fas fa-check"></i></button>';
        row['Reject'] = '<button class="btn btn-danger btn-circle btn-sm reject-button"><i class="fas fa-trash"></i></button>';
    });
};

$(document).ready(function() {
    // Make the DataTable
    let data = add_buttons(appointment_requests)
    $('#appointmentRequests').DataTable(
        {
            data: appointment_requests,
            columns: make_columns(appointment_requests),
        }
    );

    // $('#appointmentRequests').DataTable().columns([0,1]).visible(false);
    
    $('#appointmentRequests').DataTable().on('click', '.accept-button', function() {
        let data = $('#appointmentRequests').DataTable().row($(this).parents('tr')).data();
        console.log(data);
    });

    $('#appointmentRequests').DataTable().on('click', '.reject-button', function() {
        let data = $('#appointmentRequests').DataTable().row($(this).parents('tr')).data();
        console.log(data);
    });
    
});