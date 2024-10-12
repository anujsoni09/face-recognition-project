const originalVideo = document.querySelector('#original-video');
const processedImage = document.querySelector('#processed-image');
const startBtn = document.querySelector('#start-btn');
const stopBtn = document.querySelector('#stop-btn');
const captureBtn = document.querySelector('#capture-btn');
const capturedFacesContainer = document.querySelector('#captured-faces');
let mediaStream = null;
let currentFrameData = null;
let isProcessing = false;

startBtn.addEventListener('click', () => {
  initializeCamera();
});

stopBtn.addEventListener('click', () => {
  stopCamera();
});

captureBtn.addEventListener('click', () => {
  captureUnknownFace();
});

async function initializeCamera() {
  if (!mediaStream) {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: false, video: true });
      originalVideo.srcObject = mediaStream;
      startBtn.setAttribute('hidden', true);
      stopBtn.removeAttribute('hidden');
      captureBtn.removeAttribute('hidden');
      startFrameProcessing();
    } catch (error) {
      alert(`${error.name}: ${error.message}`);
      console.error(error);
    }
  }
}

function stopCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
    originalVideo.srcObject = null;
    stopBtn.setAttribute('hidden', true);
    startBtn.removeAttribute('hidden');
    captureBtn.setAttribute('hidden', true);
  }
}

async function startFrameProcessing() {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  const videoTrack = mediaStream.getVideoTracks()[0];
  const videoSettings = videoTrack.getSettings();
  canvas.width = videoSettings.width;
  canvas.height = videoSettings.height;

  const processFrame = async () => {
    if (isProcessing) {
      requestAnimationFrame(processFrame);
      return;
    }

    isProcessing = true;
    context.drawImage(originalVideo, 0, 0, canvas.width, canvas.height);
    currentFrameData = canvas.toDataURL('image/jpeg');

    try {
      const response = await fetch('/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: currentFrameData })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const result = await response.json();
      const processedImageData = result.processed_image;

      processedImage.src = processedImageData;

    } catch (error) {
      console.error('Error sending frame to backend:', error);
    } finally {
      isProcessing = false;
    }

    requestAnimationFrame(processFrame);
  };

  processFrame();
}

async function captureUnknownFace() {
  try {
    const response = await fetch('/capture_unknown', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: currentFrameData })
    });

    if (!response.ok) throw new Error('Network response was not ok');

    const result = await response.json();
    const unknownFaceImage = result.unknown_face_image;

    if (unknownFaceImage) {
      const imgWrapper = document.createElement('div'); // Create a wrapper for the image and buttons
      imgWrapper.style.position = 'relative'; // Enable absolute positioning for buttons

      const img = document.createElement('img');
      img.src = unknownFaceImage;
      img.className = 'captured-image';
      imgWrapper.appendChild(img);

      // Save button
      const saveButton = document.createElement('button');
      saveButton.textContent = 'Save Image';
      saveButton.className = 'save-button';
      saveButton.addEventListener('click', () => {
          const username = prompt('Enter username to save the image:');
          if (username) {
              saveUnknownImage(unknownFaceImage, username); // Pass the image source and username
          }
      });
      imgWrapper.appendChild(saveButton);

      // Remove button
      const removeButton = document.createElement('button');
      removeButton.textContent = 'Delete';
      removeButton.className = 'remove-button';
      removeButton.addEventListener('click', () => {
          imgWrapper.remove(); // Remove the entire wrapper (image + buttons)
      });
      imgWrapper.appendChild(removeButton);

      capturedFacesContainer.appendChild(imgWrapper); // Append the wrapper to the container
    } else {
      alert("No unknown face detected");
    }

  } catch (error) {
    console.error('Error capturing unknown face:', error);
  }
}

// Placeholder function to save the unknown image
async function saveUnknownImage(imageSrc, username) {
try {
const response = await fetch('/save_image', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ image: imageSrc, username: username })
});

if (!response.ok) throw new Error('Network response was not ok');

const result = await response.json();
alert(result.message); // Notify the user of success or failure
if (mediaStream) {
  startFrameProcessing();
}
} catch (error) {
console.error('Error saving image:', error);
}
}
