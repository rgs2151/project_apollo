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
                    <div class="file-item m-2 shadow" style="cursor: pointer" data-doc_id="${file.id}" data-session="${file.session}" data-created="${String(file.created_at).slice(0,10) + "\n" + String(file.created_at).slice(11,19)}">
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

            // select the first fileItem and click it
            $fileItems.find('.file-item').last().click();

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
    

    function transformDataToWordCloud(data) {
        const wordCounts = {};
    
        data.forEach(item => {
            const words = `${item.i_parameter_label} ${item.parameter_type} ${item.parameter_value}`.split(' ');
    
            words.forEach(word => {
                if (wordCounts[word]) {
                    wordCounts[word]++;
                } else {
                    wordCounts[word] = 1;
                }
            });
        });
    
        const wordsArray = Object.keys(wordCounts).map(key => ({
            key: key,
            value: wordCounts[key]
        }));
    
        return wordsArray;
    }

    function make_word_cloud(session){
        // get the session data
        $.ajax({
            url: window.location.origin + '/conversation/keyinformation/?session=' + session,
            xhrFields: { withCredentials: true },
            contentType: 'application/json',
            type: 'get',
            success: function(response) {
                console.log('Session data retrieved successfully!');
                console.log(response);
                
                const words = transformDataToWordCloud(response.data);

                const chart = new Chart(document.getElementById("wordCloudChart").getContext("2d"), {
                    type: "wordCloud",
                    data: {
                        labels: words.map((d) => d.key),
                        datasets: [
                        {
                            label: "",
                            data: words.map((d) => 10 + d.value * 10)
                        }
                        ]
                    },
                    options: {
                        title: {
                        display: false,
                        text: "Chart.js Word Cloud"
                        },
                        plugins: {
                        legend: {
                            display: false
                        }
                        }
                    }
                });
                  
            },
            error: function(response) {
                console.log('Failed to retrieve session data.');
            }
        });
    }

    function make_file_inspector( doc_id, session, created, prev_img){
        return `
            <div class="row p-2">
                <!-- Left side: Preview Image -->
                <div class="col-4 text-center">
                    <img src="${prev_img}" class="inspect_img shadow" alt="Document Preview">
                    <div class="col-12 p-2">
                        <button class="btn btn-secondary btn-sm"><i class="far fa-file-pdf"></i> Open</button>
                        <button class="btn btn-primary btn-sm"><i class="fas fa-download"></i> Download</button>
                    </div>
                </div>
                <!-- Right side: Document Info -->
                <div class="col-8">
                    <div class="row mb-2">
                        <div class="col-12">
                            <h5>Document: ${doc_id}</h5>
                            <p>Created at: ${created}</p>
                        </div>

                    </div>
                    <div class="row">
                        <div class="col-12">
                            <canvas id="wordCloudChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    $('#file-items').on('click', '.file-item', function() {
        var document_id = $(this).data('doc_id');
        var session = $(this).data('session');
        var created = $(this).data('created');

        var prev_img = $(this).find('img').attr('src');

        console.log('clicked on ', document_id, session, created);

        let inspect_divs = make_file_inspector(document_id, session, created, prev_img);

        $('#inspect-section').html(inspect_divs);

        make_word_cloud(session);

    });
});
