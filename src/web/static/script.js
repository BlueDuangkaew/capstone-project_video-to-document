// Enhanced upload form handling with drag & drop
const uploadForm = document.getElementById("uploadForm");
const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const statusDiv = document.getElementById("status");

// Drag and drop functionality
if (uploadArea) {
    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = "#667eea";
        uploadArea.style.background = "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)";
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.style.borderColor = "#d1d5db";
        uploadArea.style.background = "linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)";
    });

    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = "#d1d5db";
        uploadArea.style.background = "linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%)";
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            updateFileName(files[0].name);
        }
    });

    // Update file name display
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            updateFileName(e.target.files[0].name);
        }
    });
}

function updateFileName(fileName) {
    const uploadText = document.querySelector(".upload-text");
    if (uploadText) {
        uploadText.textContent = `Selected: ${fileName}`;
        uploadText.style.color = "#667eea";
    }
}

// Form submission
if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const file = fileInput.files[0];
        if (!file) {
            showStatus("Please select a video file first.", "error");
            return;
        }

        // Validate file type
        const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-msvideo'];
        if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov)$/i)) {
            showStatus("Please select a valid video file (MP4, AVI, or MOV).", "error");
            return;
        }

        const formData = new FormData();
        formData.append("video", file);

        // Show uploading status with animation
        showStatus("Uploading your video...", "loading");
        
        // Disable form during upload
        const submitBtn = uploadForm.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.6";
        submitBtn.style.cursor = "not-allowed";

        try {
            // Upload video
            const res = await fetch("/upload/", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                throw new Error(`Upload failed: ${res.statusText}`);
            }

            const data = await res.json();
            
            showStatus("Processing started! Redirecting...", "success");

            // Redirect to progress page after a brief delay
            setTimeout(() => {
                window.location.href = `/progress/${data.job_id}`;
            }, 1000);

        } catch (error) {
            console.error("Upload error:", error);
            showStatus(`Upload failed: ${error.message}. Please try again.`, "error");
            
            // Re-enable form
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
            submitBtn.style.cursor = "pointer";
        }
    });
}

function showStatus(message, type) {
    if (!statusDiv) return;
    
    statusDiv.textContent = message;
    statusDiv.style.display = "block";
    
    // Style based on status type
    switch(type) {
        case "loading":
            statusDiv.style.background = "linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)";
            statusDiv.style.color = "#667eea";
            statusDiv.style.border = "2px solid #667eea";
            break;
        case "success":
            statusDiv.style.background = "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)";
            statusDiv.style.color = "#065f46";
            statusDiv.style.border = "2px solid #10b981";
            break;
        case "error":
            statusDiv.style.background = "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)";
            statusDiv.style.color = "#991b1b";
            statusDiv.style.border = "2px solid #ef4444";
            break;
    }
}