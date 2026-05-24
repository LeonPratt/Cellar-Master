const video = document.getElementById('previewVideo');
const canvas = document.getElementById('hiddenCanvas');
const switchCameraButton = document.getElementById('switchCameraButton');
const captureButton = document.getElementById('captureButton');
const statusText = document.getElementById('statusText');

let currentStream = null;
let videoDevices = [];
let currentFacingMode = 'environment';
let capturedBlob = null;

function updateStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? '#ff6b6b' : '#f1f1f1';
}

function getUserMedia(constraints) {
  if (navigator.mediaDevices?.getUserMedia) {
    return navigator.mediaDevices.getUserMedia(constraints);
  }

  const legacyGetUserMedia =
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia;

  if (!legacyGetUserMedia) {
    return Promise.reject(new Error('getUserMedia is not available'));
  }

  return new Promise((resolve, reject) => {
    legacyGetUserMedia.call(navigator, constraints, resolve, reject);
  });
}

async function listVideoDevices() {
  if (!navigator.mediaDevices?.enumerateDevices) {
    return;
  }

  const devices = await navigator.mediaDevices.enumerateDevices();
  videoDevices = devices.filter((device) => device.kind === 'videoinput');
}

async function stopStream() {
  if (!currentStream) return;
  currentStream.getTracks().forEach((track) => track.stop());
  currentStream = null;
}

function getVideoConstraints() {
  return {
    facingMode: { ideal: currentFacingMode },
    width: { ideal: 1280 },
    height: { ideal: 720 },
  };
}

async function startCamera() {
  await stopStream();

  const constraints = {
    video: getVideoConstraints(),
    audio: false,
  };

  currentStream = await getUserMedia(constraints);
  video.srcObject = currentStream;
  await video.play();
}

function isSecureContextOfferReasonable() {
  if (window.isSecureContext) return true;
  const hostname = window.location.hostname;
  return hostname === 'localhost' || hostname === '127.0.0.1';
}

async function initCamera() {
  if (!getUserMedia) {
    updateStatus('Camera not supported in this browser.', true);
    captureButton.disabled = true;
    switchCameraButton.disabled = true;
    return;
  }

  if (!isSecureContextOfferReasonable()) {
    updateStatus('Camera requires HTTPS on iOS. Open this page using HTTPS or localhost.', true);
    captureButton.disabled = true;
    switchCameraButton.disabled = true;
    return;
  }

  try {
    await listVideoDevices();
    await startCamera();
    updateStatus(videoDevices.length > 1 ? `Using ${currentFacingMode} camera` : 'Camera ready');
    switchCameraButton.disabled = videoDevices.length <= 1;
  } catch (error) {
    updateStatus(error.message || 'Unable to start camera.', true);
    captureButton.disabled = true;
    switchCameraButton.disabled = true;
  }
}

function capturePhoto() {
  if (!video.videoWidth || !video.videoHeight) {
    updateStatus('Video is not ready yet. Please wait a moment.', true);
    return;
  }

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const context = canvas.getContext('2d');
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(async (blob) => {
    if (!blob) {
      updateStatus('Could not capture image.', true);
      return;
    }

    capturedBlob = blob;
    updateStatus('Photo captured. Sending to server...');
    captureButton.disabled = true;
    await sendPhoto();
    captureButton.disabled = false;
  }, 'image/png');
}

async function sendPhoto() {
  if (!capturedBlob) {
    updateStatus('No photo to send.', true);
    return;
  }

  const formData = new FormData();
  formData.append('photo', capturedBlob, 'photo.png');

  try {
    const response = await fetch('/upload-photo', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Server returned ${response.status}`);
    }

    const result = await response.json().catch(() => null);
    updateStatus(result?.message || 'Photo uploaded successfully.');
  } catch (error) {
    updateStatus(`Upload failed: ${error.message}`, true);
  }
}

async function switchCamera() {
  if (videoDevices.length <= 1) return;

  currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
  updateStatus('Switching camera...');

  try {
    await startCamera();
    updateStatus(`Using ${currentFacingMode} camera`);
  } catch (error) {
    updateStatus(error.message || 'Unable to switch camera.', true);
  }
}

switchCameraButton.addEventListener('click', switchCamera);
captureButton.addEventListener('click', capturePhoto);

initCamera();
