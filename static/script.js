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
let countdownValue = 21;
let countdownInterval = null;
let customVideoDuration = null;

const videoPlayer = document.getElementById('videoPlayer');
const trafficLights = document.querySelectorAll('.traffic-light');
const countdownTimer = document.querySelector('.countdown-timer');
const countdownTimerLeft = document.querySelector('.top-left');
const predictionSeconds = document.querySelector('.top-right');

// Function to update traffic lights
function updateTrafficLights(activeIndex) {
    trafficLights.forEach((light, index) => {
        const redLight = light.querySelector('.light.red');
        const yellowLight = light.querySelector('.light.yellow');
        const greenLight = light.querySelector('.light.green');

        redLight.classList.remove('active');
        yellowLight.classList.remove('active');
        greenLight.classList.remove('active');

        if (index === activeIndex) {
            greenLight.classList.add('active');
        } else {
            redLight.classList.add('active');
        }
    });
}

// Function to start countdown
function startCountdown(durationOverride = null) {
    const duration = durationOverride !== null ? durationOverride : videoPlayer.duration;
    countdownValue = Math.ceil(duration);
    countdownTimer.textContent = countdownValue;

    if (countdownInterval) {
        clearInterval(countdownInterval);
    }

    countdownInterval = setInterval(() => {
        countdownValue--;
        countdownTimer.textContent = countdownValue;

        if (countdownValue <= 0) {
            clearInterval(countdownInterval);
        }
    }, 1000);
}

// Function to play next video
function playNextVideo() {
    customVideoDuration = null;
    yoloExecuted = false;

    trafficLights.forEach(light => {
        light.querySelector('.light.green').classList.remove('active');
        light.querySelector('.light.red').classList.add('active');
    });

    currentVideoIndex = (currentVideoIndex + 1) % videoPaths.length;
    videoPlayer.src = videoPaths[currentVideoIndex];

    videoPlayer.onloadeddata = () => {
        videoPlayer.play().then(() => {
            updateTrafficLights(currentVideoIndex);
            startCountdown(customVideoDuration);
        }).catch(error => {
            console.error('Error playing video:', error);
            setTimeout(playNextVideo, 1000);
        });
    };
}

// Function to run YOLO
async function runYOLO() {
    if (yoloExecuted) return null;

    try {
        const nextVideoIndex = (currentVideoIndex + 1) % videoPaths.length;
        const videoPath = videoPaths[nextVideoIndex];

        console.log(`Running YOLO on video: ${videoPath}`);

        const hiddenVideo = document.createElement('video');
        hiddenVideo.src = videoPath;
        hiddenVideo.crossOrigin = 'anonymous';
        hiddenVideo.muted = true;
        hiddenVideo.playsInline = true;
        hiddenVideo.style.display = 'none';
        document.body.appendChild(hiddenVideo);

        await new Promise((resolve, reject) => {
            hiddenVideo.onloadeddata = () => {
                hiddenVideo.currentTime = 0;
                resolve();
            };
            hiddenVideo.onerror = reject;
        });

        await new Promise(resolve => {
            hiddenVideo.onseeked = resolve;
        });

        const canvas = document.createElement('canvas');
        canvas.width = hiddenVideo.videoWidth;
        canvas.height = hiddenVideo.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(hiddenVideo, 0, 0, canvas.width, canvas.height);

        const imageBase64 = canvas.toDataURL('image/jpeg');
        hiddenVideo.remove();

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
        yoloExecuted = true;
        predictionSeconds.textContent = result.nextDuration;

    } catch (error) {
        console.error("runYOLO error:", error);
        return null;
    }
}

// Time update logic
videoPlayer.addEventListener('timeupdate', () => {
    const effectiveDuration = customVideoDuration !== null ? customVideoDuration : videoPlayer.duration;
    const currentTime = videoPlayer.currentTime;

    // Run YOLO 3 seconds before effective end
    if (effectiveDuration - currentTime <= 3 && !yoloExecuted) {
        runYOLO().then(durationOverride => {
            if (durationOverride !== null) {
                customVideoDuration = durationOverride;
                console.log(`Custom duration from YOLO: ${customVideoDuration}`);
            }
        });
    }

    // Stop video early if custom duration reached
    if (customVideoDuration !== null && currentTime >= customVideoDuration) {
        videoPlayer.pause();
        videoPlayer.dispatchEvent(new Event('ended'));
    }
});

// Event handlers
videoPlayer.addEventListener('ended', () => {
    console.log('Video ended, switching to next video');
    playNextVideo();
});

videoPlayer.addEventListener('error', (e) => {
    console.error('Video error:', e);
    playNextVideo();
});

videoPlayer.addEventListener('loadedmetadata', () => {
    startCountdown(customVideoDuration);
});

// Initialize video playback
function initializeVideo() {
    customVideoDuration = null;
    videoPlayer.src = videoPaths[0];

    videoPlayer.onloadeddata = () => {
        videoPlayer.play().then(() => {
            updateTrafficLights(0);
            startCountdown(customVideoDuration);
        }).catch(error => {
            console.error('Error playing initial video:', error);
            setTimeout(playNextVideo, 1000);
        });
    };
}

initializeVideo();

// Pause video if user closes window
window.addEventListener('beforeunload', () => {
    videoPlayer.pause();
    videoPlayer.src = '';
});

