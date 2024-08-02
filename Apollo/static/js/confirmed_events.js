// Shelf section
$(document).ready(function() {
    // Mock data endpoint (replace with actual endpoint)
    const dataEndpoint = window.location.origin + '/conversation/shared-documents-get/';
    console.log(global_client_user_id);
    // Load files via AJAX
    $.ajax({
        url: dataEndpoint,
        headers: {'Content-Type': 'application/json'},
        xhrFields: { withCredentials: true },
        type: 'post',
        data: JSON.stringify({"user_id": global_client_user_id}),
        success: function(response) {
            console.log(response);
            if (response.length === 0) {
                $('#file-items').html('<div class="text-center">No files shared.</div>');
                return;
            }
            const $fileItems = $('#file-items');
            response.forEach(file => {
                const fileItem = `
                    <div class="file-item m-2" style="cursor: pointer" data-doc_id="${file.id}" data-session="${file.session}" data-created="${String(file.created_at).slice(0,10) + "\n" + String(file.created_at).slice(11,19)}">
                        <div class="card h-100">
                            <div class="position-relative">
                                <img src="data:image/png;base64,${file.document_preview_bytes}" class="card-img-top img-thumbnail" alt="File preview">
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

            // select one fileintem and click it
            $('.file-item').last().click();
        },
        error: function() {
            console.log('Failed to load files.');
        }
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

                if (response.data.length === 0) {
                    console.log('No data to display.');
                    return;
                }
                 

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
                <div class="col-6 text-center">
                    <img src="${prev_img}" class="inspect_img shadow" alt="Document Preview">
                    <div class="col-12 p-2">
                        <button class="btn btn-secondary btn-sm"><i class="far fa-file-pdf"></i> Open</button>
                        <button class="btn btn-primary btn-sm"><i class="fas fa-download"></i> Download</button>
                    </div>
                </div>
                <!-- Right side: Document Info -->
                <div class="col-6">
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
