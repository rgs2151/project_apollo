
// Shelf section
$(document).ready(function() {
    // // Mock data endpoint (replace with actual endpoint)
    // const dataEndpoint = '/get-files';

    // // Load files via AJAX
    // $.ajax({
    //     url: dataEndpoint,
    //     method: 'GET',
    //     success: function(response) {
    //         const $fileItems = $('#file-items');
    //         response.files.forEach(file => {
    //             const fileItem = `
    //                 <div class="col-3 mb-3">
    //                     <div class="card h-100">
    //                         <div class="position-relative">
    //                             <img src="${file.image_url}" class="card-img-top img-thumbnail" alt="File preview">
    //                             <button class="btn btn-sm ${file.shared ? 'btn-primary' : 'btn-secondary'} position-absolute top-0 end-0 toggle-share" data-shared="${file.shared}">
    //                                 ${file.shared ? 'Shareable' : 'Not Shareable'}
    //                             </button>
    //                         </div>
    //                         <div class="card-body text-center">
    //                             <p class="card-text">${file.description}</p>
    //                             <small class="text-muted">${file.timestamp}</small>
    //                         </div>
    //                     </div>
    //                 </div>
    //             `;
    //             $fileItems.append(fileItem);
    //         });
    //     },
    //     error: function() {
    //         alert('Failed to load files.');
    //     }
    // });

    let files = [
        {
            'image_url': 'https://images.template.net/wp-content/uploads/2017/06/Medical-Emergency-Incident-Report.jpg',
            'description': 'PDF Document 1',
            'timestamp': '2024-07-01 12:00',
            'shared': true
        },
        {
            'image_url': 'https://images.template.net/wp-content/uploads/2017/06/Medical-Emergency-Incident-Report.jpg',
            'description': 'PDF Document 2',
            'timestamp': '2024-07-02 14:30',
            'shared': false
        },
        {
            'image_url': 'https://images.template.net/wp-content/uploads/2017/06/Medical-Emergency-Incident-Report.jpg',
            'description': 'PDF Document 3',
            'timestamp': '2024-07-03 16:45',
            'shared': true
        },
        {
            'image_url': 'https://images.template.net/wp-content/uploads/2017/06/Medical-Emergency-Incident-Report.jpg',
            'description': 'PDF Document 4',
            'timestamp': '2024-07-04 10:20',
            'shared': false
        },
        {
            'image_url': 'https://images.template.net/wp-content/uploads/2017/06/Medical-Emergency-Incident-Report.jpg',
            'description': 'PDF Document 4',
            'timestamp': '2024-07-04 10:20',
            'shared': false
        },
        
    ]

    const $fileItems = $('#file-items');
    files.forEach(file => {
        const fileItem = `
            <div class="file-item m-2">
                <div class="card h-100">
                    <div class="position-relative">
                        <img src="${file.image_url}" class="card-img-top img-thumbnail" alt="File preview">
                    </div>
                    <div class="card-body text-center">
                        <p class="card-text">${file.description}</p>
                        <small class="text-muted">${file.timestamp}</small>
                    </div>
                </div>
            </div>
        `;
        $fileItems.append(fileItem);
    });
});
