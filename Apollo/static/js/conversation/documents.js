// Upload section
$(document).ready(function() {
    const $uploadSection = $('#upload-section');
    const $initialUpload = $('#initial-upload');
    const $fileUploaded = $('#file-uploaded');
    const $uploadButton = $('#upload-button');
    const $submitButton = $('#submit-button');
    let uploadedFile;

    // Simulate file upload button click
    $uploadButton.on('click', function() {
        // Here you can trigger a file input click if you have one hidden for manual upload
        $('#file-input').click();
    });

    // Handle file input change
    $('#file-input').on('change', function(event) {
        uploadedFile = event.target.files[0];
        handleFileUpload();
    });

    // Handle drag and drop functionality
    $uploadSection.on('dragover', function(event) {
        event.preventDefault();
        $uploadSection.addClass('drag-over');
    });

    $uploadSection.on('dragleave', function() {
        $uploadSection.removeClass('drag-over');
    });

    $uploadSection.on('drop', function(event) {
        event.preventDefault();
        $uploadSection.removeClass('drag-over');
        uploadedFile = event.originalEvent.dataTransfer.files[0];
        handleFileUpload();
    });

    // Handle file upload and UI change
    function handleFileUpload() {
        if (uploadedFile) {
            $initialUpload.addClass('d-none');
            $fileUploaded.removeClass('d-none');

            $('#file-name').text(uploadedFile.name);
            // Optionally show file name or other details here
            console.log('Uploaded file:', uploadedFile);
        }
    }

    // Handle submit action
    $submitButton.on('click', function() {
        // Handle form submission or further processing of uploadedFile
        $initialUpload.removeClass('d-none');
        $fileUploaded.addClass('d-none');
        uploadedFile = null;
    });
});


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
                        <button class="btn btn-circle ${file.shared ? 'btn-primary' : 'btn-secondary'} position-absolute top-0 end-0 toggle-share" data-shared="${file.shared}">
                            ${file.shared ? '<i class="fas fa-lock-open"></i>' : '<i class="fas fa-lock"></i>'}
                        </button>
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

    // Handle toggling share button
    $('#file-items').on('click', '.toggle-share', function() {
        const $button = $(this);
        const isShared = $button.data('shared');
        
        if (isShared) {
            $button.html('<i class="fas fa-lock"></i>').removeClass('btn-primary').addClass('btn-secondary');
        } else {
            $button.html('<i class="fas fa-lock-open"></i>').removeClass('btn-secondary').addClass('btn-primary');
        }
        
        $button.data('shared', !isShared);
    });
});
