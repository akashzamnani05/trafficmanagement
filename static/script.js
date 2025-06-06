// Video paths
const videoPaths = [
    "static/vids/new1.mp4",
    "static/vids/new2.mp4",
    "static/vids/new3.mp4",
    "static/vids/new2.mp4",
];

// Mask paths
const maskPaths = [
    "static/masks/new1mask.png",
    'static/masks/new2mask.png',
    "static/masks/new3mask.png",
    "static/masks/new2mask.png"
];

let currentVideoIndex = 0;
let yoloExecuted = false;
const videoPlayer = document.getElementById('videoPlayer');
const trafficLights = document.querySelectorAll('.traffic-light');
const countdownTimer = document.querySelector('.countdown-timer');

let countdownInterval;
let countdownValue = 21;

// Function to update traffic lights
function updateTrafficLights(activeIndex) {
    trafficLights.forEach((light, index) => {
        const redLight = light.querySelector('.light.red');
        const yellowLight = light.querySelector('.light.yellow');
        const greenLight = light.querySelector('.light.green');

        // Reset all lights
        redLight.classList.remove('active');
        yellowLight.classList.remove('active');
        greenLight.classList.remove('active');

        // Set active light
        if (index === activeIndex) {
            greenLight.classList.add('active');
        } else {
            redLight.classList.add('active');
        }
    });
}

// Function to start countdown
function startCountdown() {
    // Get video duration and set countdown
    const duration = videoPlayer.duration;
    countdownValue = Math.ceil(duration);
    countdownTimer.textContent = countdownValue;
    
    // Clear any existing interval
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    
    // Start new countdown
    countdownInterval = setInterval(() => {
        countdownValue--;
        countdownTimer.textContent = countdownValue;
        
        if (countdownValue <= 0) {
            clearInterval(countdownInterval);
        }
    }, 1000);
}

// Function to handle video playback
function playNextVideo() {
    // Turn all signals red before switching
    trafficLights.forEach(light => {
        light.querySelector('.light.green').classList.remove('active');
        light.querySelector('.light.red').classList.add('active');
    });
    
    // Update to next video
    currentVideoIndex = (currentVideoIndex + 1) % videoPaths.length;
    videoPlayer.src = videoPaths[currentVideoIndex];
    
    // Wait for video to load
    videoPlayer.onloadeddata = () => {
        videoPlayer.play().then(() => {
            // Update traffic lights after video starts playing
            updateTrafficLights(currentVideoIndex);
            // Start countdown when video starts
            startCountdown();
        }).catch(error => {
            console.error('Error playing video:', error);
            // Try next video if current one fails
            setTimeout(playNextVideo, 1000);
        });
    };
    
    yoloExecuted = false;
}

async function runYOLO() {
    if (yoloExecuted) return;

    try {
        // Get the next video index (circular)
        const nextVideoIndex = (currentVideoIndex + 1) % videoPaths.length;
        const videoPath = videoPaths[nextVideoIndex];

        // Create a hidden video element to extract the first frame
        const hiddenVideo = document.createElement('video');
        hiddenVideo.src = videoPath;
        hiddenVideo.crossOrigin = 'anonymous'; // Allow canvas access
        hiddenVideo.muted = true;
        hiddenVideo.playsInline = true;
        hiddenVideo.style.display = 'none';
        document.body.appendChild(hiddenVideo);

        // Wait for metadata to load and seek to 0
        await new Promise((resolve, reject) => {
            hiddenVideo.onloadeddata = () => {
                hiddenVideo.currentTime = 0;
                resolve();
            };
            hiddenVideo.onerror = reject;
        });

        // Wait for frame to load
        await new Promise((resolve) => {
            hiddenVideo.onseeked = resolve;
        });

        // Draw the first frame on a canvas
        const canvas = document.createElement('canvas');
        canvas.width = hiddenVideo.videoWidth;
        canvas.height = hiddenVideo.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(hiddenVideo, 0, 0, canvas.width, canvas.height);

        // Convert to base64
        const imageBase64 = canvas.toDataURL('image/jpeg');

        // Clean up
        hiddenVideo.remove();

        // Send to Flask backend
        const response = await fetch('/process_frame', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: imageBase64,
                index: nextVideoIndex
            })
        });

        const result = await response.json();
        // console.log("YOLO result:", result);

        yoloExecuted = true;
    } catch (error) {
        console.error("runYOLO error:", error);
    }
}

// Event listeners
videoPlayer.addEventListener('timeupdate', () => {
    const duration = videoPlayer.duration;
    const currentTime = videoPlayer.currentTime;
    
    // Run YOLO 3 seconds before the video ends
    if (duration - currentTime <= 3 && !yoloExecuted) {
        runYOLO();
        console.log('running yolo ')
    }
});

videoPlayer.addEventListener('ended', () => {
    console.log('Video ended, switching to next video');
    playNextVideo();
});

videoPlayer.addEventListener('error', (e) => {
    console.error('Video error:', e);
    playNextVideo();
});

videoPlayer.addEventListener('loadedmetadata', () => {
    startCountdown();
});

// Initialize the first video
function initializeVideo() {
    videoPlayer.src = videoPaths[0];
    videoPlayer.onloadeddata = () => {
        videoPlayer.play().then(() => {
            updateTrafficLights(0);
            startCountdown();
        }).catch(error => {
            console.error('Error playing initial video:', error);
            setTimeout(playNextVideo, 1000);
        });
    };
}

// Start the application
initializeVideo();

// Handle window closing
window.addEventListener('beforeunload', () => {
    videoPlayer.pause();
    videoPlayer.src = '';
}); 
