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
                    <div class="file-item m-2">
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
        },
        error: function() {
            console.log('Failed to load files.');
        }
    });
});
