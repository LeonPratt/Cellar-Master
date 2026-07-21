const video = document.getElementById('previewVideo');
const canvas = document.getElementById('hiddenCanvas');
const switchCameraButton = document.getElementById('switchCameraButton');
const captureButton = document.getElementById('captureButton');
const uploadButton = document.getElementById('uploadButton');
const uploadInput = document.getElementById('uploadInput');
const statusText = document.getElementById('statusText');
const errorPopup = document.getElementById('errorPopup');
const errorPopupMessage = document.getElementById('errorPopupMessage');
const errorPopupClose = document.getElementById('errorPopupClose');
const cameraStepTitle = document.querySelector('[data-camera-step-title]');
const cameraGuidance = document.querySelector('[data-camera-guidance]');
const uploadTestMode = new URLSearchParams(window.location.search).get('test_error') === '1';

let currentStream = null;
let videoDevices = [];
let currentFacingMode = 'environment';
let frontLabelBlob = null;
let backLabelBlob = null;

function updateStatus(message, isError = false) {
  //statusText.textContent = message;
  //statusText.style.color = isError ? '#ff6b6b' : '#f1f1f1';
  console.log(`Status: ${message}`);
}

function showErrorPopup(message) {
  errorPopupMessage.textContent = message;
  errorPopup.style.visibility = 'visible';
}

function hideErrorPopup() {
  errorPopup.style.visibility = 'hidden';
  window.location.href = `${window.location.pathname}${window.location.search}`;
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
    updateStatus('Camera not supported in this browser. You can still upload an image.', true);
    captureButton.disabled = true;
    switchCameraButton.disabled = true;
    return;
  }

  if (!isSecureContextOfferReasonable()) {
    updateStatus('Camera requires HTTPS on iOS. You can still upload an image.', true);
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

function setCaptureStep(isBackLabel) {
  cameraStepTitle.textContent = isBackLabel ? 'Capture the back label' : 'Capture the front label';
  cameraGuidance.textContent = isBackLabel
    ? 'Turn the bottle around and capture the back label, including any details or barcode.'
    : 'Centre the front label in the frame, then capture a clear photo.';
  uploadButton.setAttribute('aria-label', isBackLabel ? 'Upload back label image' : 'Upload front label image');
  captureButton.setAttribute('aria-label', isBackLabel ? 'Capture back label' : 'Capture front label');
}

async function finalizeLabelCapture(blob, previewFilename) {
  if (!frontLabelBlob) {
    frontLabelBlob = blob;
    setCaptureStep(true);
    updateStatus(previewFilename ? `Front label uploaded: ${previewFilename}. Now capture the back label.` : 'Front label captured. Now capture the back label.');
    return;
  }

  backLabelBlob = blob;

  video.style.visibility = 'hidden';

  const postCaptureImage = document.getElementById('PostCaptureImage');
  postCaptureImage.src = URL.createObjectURL(backLabelBlob);
  postCaptureImage.style.display = 'flex';

  const div = document.getElementById('overlayDiv');
  div.style.display = 'flex';

  captureButton.style.display = 'none';
  uploadButton.style.display = 'none';
  switchCameraButton.style.display = 'none';
  updateStatus(previewFilename ? `Back label uploaded: ${previewFilename}. Sending both labels to server...` : 'Back label captured. Sending both labels to server...');
  captureButton.disabled = true;
  uploadButton.disabled = true;
  await sendPhotos();
  captureButton.disabled = false;
  uploadButton.disabled = false;
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

    await finalizeLabelCapture(blob);
  }, 'image/png');
}

async function handleUploadSelection() {
  const [file] = uploadInput.files || [];
  if (!file) {
    return;
  }

  await finalizeLabelCapture(file, file.name);
  uploadInput.value = '';
}

async function sendPhotos() {
  if (!frontLabelBlob || !backLabelBlob) {
    updateStatus('Both label photos are required.', true);
    showErrorPopup('Please capture both the front and back labels before continuing.');
    return;
  }

  const formData = new FormData();
  formData.append('photo-front', frontLabelBlob, 'front-label.png');
  formData.append('photo-back', backLabelBlob, 'back-label.png');

  try {
    const uploadUrl = new URL('/upload-photo', window.location.origin);
    if (uploadTestMode) {
      uploadUrl.searchParams.set('test_error', '1');
    }

    const response = await fetch(uploadUrl.toString(), {
      method: 'POST',
      body: formData,
    });

    const responseText = await response.text();

    if (!response.ok) {
      let errorBody = null;
      try {
        errorBody = responseText ? JSON.parse(responseText) : null;
      } catch {
        errorBody = null;
      }

      throw new Error(errorBody?.message || responseText || `The server could not process that image. (${response.status})`);
    }

    const result = responseText ? JSON.parse(responseText) : null;


    updateStatus(result?.message || 'Photo uploaded successfully.');

    const url = new URL(window.location.href);
    console.log(result)
    url.pathname += "/verify/";
    url.searchParams.delete('test_error');
    url.searchParams.set("img", result.filename);
    url.searchParams.set("name", result.name);
    url.searchParams.set("grape_variety", result.grape_variety);
    url.searchParams.set("region", result.region);
    url.searchParams.set("year", result.year);
    url.searchParams.set("producer", result.producer);
    url.searchParams.set("status", "success");

    window.location.href = url.toString();
  } catch (error) {
    const message = error.message || 'The image could not be processed.';
    updateStatus(`Upload failed: ${message}`, true);
    showErrorPopup(message);
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
uploadButton.addEventListener('click', () => uploadInput.click());
uploadInput.addEventListener('change', handleUploadSelection);
errorPopupClose.addEventListener('click', hideErrorPopup);
errorPopup.addEventListener('click', (event) => {
  if (event.target === errorPopup) {
    hideErrorPopup();
  }
});

initCamera();
