document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const photo = document.getElementById('photo');
    
    // Controls
    const cameraControls = document.getElementById('camera-controls');
    const postCaptureControls = document.getElementById('post-capture-controls');
    
    // Buttons
    const captureButton = document.getElementById('capture-button');
    const retakeButton = document.getElementById('retake-button');
    const analyzeButton = document.getElementById('analyze-button');
    const rotateButton = document.getElementById('rotate-btn');
    const uploadButton = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-input');
    
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    
    let stream = null;
    let facingMode = 'environment'; // Default to back camera

    // Initialize Camera
    async function initCamera() {
        try {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: facingMode } 
            });
            video.srcObject = stream;
            errorMessage.style.display = 'none';
            
            // Ensure video plays (sometimes needed for iOS)
            video.play().catch(e => console.log("Video play error:", e));
            
        } catch (err) {
            console.error("Error accessing camera: ", err);
            errorMessage.textContent = "Could not access camera. Please ensure you have granted permissions.";
            errorMessage.style.display = 'block';
        }
    }

    // Start camera on load
    initCamera();

    // Rotate Camera
    rotateButton.addEventListener('click', () => {
        facingMode = facingMode === 'environment' ? 'user' : 'environment';
        initCamera();
    });

    // Capture Photo
    captureButton.addEventListener('click', () => {
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const data = canvas.toDataURL('image/jpeg');
        photo.setAttribute('src', data);
        
        showPostCaptureUI();
    });

    // Upload Image
    uploadButton.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                photo.setAttribute('src', e.target.result);
                showPostCaptureUI();
            };
            reader.readAsDataURL(file);
        }
    });

    // Retake
    retakeButton.addEventListener('click', () => {
        photo.style.display = 'none';
        video.style.display = 'block';
        
        cameraControls.style.display = 'flex';
        postCaptureControls.style.display = 'none';
        
        // Restart camera if it was stopped (optional, but good practice)
        if (!stream || !stream.active) {
            initCamera();
        }
    });

    // Analyze
    analyzeButton.addEventListener('click', async () => {
        const imageData = photo.getAttribute('src');
        
        loading.style.display = 'block';
        analyzeButton.disabled = true;
        retakeButton.disabled = true;
        errorMessage.style.display = 'none';

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image_data: imageData })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                window.location.href = result.redirect_url;
            } else {
                throw new Error(result.error || 'Analysis failed');
            }
        } catch (err) {
            console.error(err);
            errorMessage.textContent = err.message;
            errorMessage.style.display = 'block';
            loading.style.display = 'none';
            analyzeButton.disabled = false;
            retakeButton.disabled = false;
        }
    });

    function showPostCaptureUI() {
        video.style.display = 'none';
        photo.style.display = 'block';
        
        cameraControls.style.display = 'none';
        postCaptureControls.style.display = 'flex';
    }
});
