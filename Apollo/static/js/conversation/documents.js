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

        if (uploadedFile){
    
            const formData = new FormData();
            formData.append('attachment', uploadedFile);

            console.log('reached here');
            
            $.ajax({
                url: window.location.origin + '/conversation/user-upload-document/',
                type: 'post',
                xhrFields: { withCredentials: true },
                data: formData,
                processData: false, // Prevents jQuery from automatically transforming the data into a query string
                contentType: false, // Prevents jQuery from setting the Content-Type header
                success: function(response) {
                    console.log('File uploaded successfully!');
                },
                error: function(response) {
                    console.log('Failed to upload file.');
                }
            });
            
        }

        // Handle form submission or further processing of uploadedFile
        $initialUpload.removeClass('d-none');
        $fileUploaded.addClass('d-none');
        uploadedFile = null;
    });
});


// Shelf section
$(document).ready(function() {
    // Mock data endpoint (replace with actual endpoint)
    const dataEndpoint = window.location.origin + '/conversation/user-documents-uploaded-dashboard/';

    // Load files via AJAX
    $.ajax({
        url: dataEndpoint,
        xhrFields: { withCredentials: true },
        method: 'get',
        success: function(response) {
            console.log(response);

            if (response.data.length === 0) {
                $('#file-items').html('<div class="text-center">No files loaded in database </div>');
                return;
            }

            const $fileItems = $('#file-items');
            response.data.forEach(file => {
                const fileItem = `
                    <div class="file-item m-2" style="cursor: pointer" data-metadata="">
                        <div class="card h-100">
                            <div class="position-relative">
                                <img src="data:image/png;base64,${file.document_preview_bytes}" class="card-img-top img-thumbnail" alt="File preview">
                                <button class="btn btn-circle ${file.shared_globaly ? 'btn-primary' : 'btn-secondary'} position-absolute top-0 end-0 toggle-share" data-shared="${file.shared_globaly}" data-doc_id="${file.id}" >
                                    ${file.shared_globaly ? '<i class="fas fa-lock-open"></i>' : '<i class="fas fa-lock"></i>'}
                                </button>
                            </div>
                            <div class="card-body text-center">
                                <p class="card-text">${file.id}</p>
                                <small class="text-muted">${String(file.created_at).slice(0,10)}</small>
                            </div>
                        </div>
                    </div>
                `;
                $fileItems.append(fileItem);
            });
        },
        error: function() {
            console.log('Failed to load files.');
        }
    });

    function update_share_status(doc_id, status){
        $.ajax({
            url: window.location.origin + '/conversation/share-document/',
            xhrFields: { withCredentials: true },
            contentType: 'application/json',
            type: 'put',
            data: JSON.stringify({
                'id': doc_id,
                'shared_globaly': status
            }),
            success: function(response) {
                console.log('File shared status updated successfully!');
            },
            error: function(response) {
                console.log('Failed to update file shared status.');
            }
        });
    }

    // Handle toggling share button
    $('#file-items').on('click', '.toggle-share', function() {
        const $button = $(this);
        const document_id = $button.data('doc_id');
        const isShared = $button.data('shared');
        console.log("is shared", document_id + " " + isShared);

        if (isShared) {
            $button.html('<i class="fas fa-lock"></i>').removeClass('btn-primary').addClass('btn-secondary');
        } else {
            $button.html('<i class="fas fa-lock-open"></i>').removeClass('btn-secondary').addClass('btn-primary');
        }
        update_share_status(document_id, !isShared);
        $button.data('shared', !isShared);
    });

    // $('#file-items').on('click', '.file-item', function() {
    //     const metadata = $(this).data('metadata');
    //     console.log('File metadata:', JSON.parse(metadata));
    // });
});
