const dropArea = document.getElementById("drop-area");
const gallery = document.getElementById('gallery');
const progressBar = document.getElementById('progress-bar');
const clearAllButton = document.getElementById('clear-all');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false);
  document.body.addEventListener(eventName, preventDefaults, false);
});

// Highlight drop area
['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
});

['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
});

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);

gallery.addEventListener('click', handleClick);

clearAllButton.addEventListener('click', clearAllImages);

function clearAllImages() {
  const images = gallery.querySelectorAll('img');

  images.forEach(img => {
    if (img.src.startsWith('blob:')) {
      URL.revokeObjectURL(img.src)
    }
  });

  gallery.innerHTML = '';
}

async function handleClick(e) {
  if(e.target.className == 'copy') {
    const src = e.target.parentElement.parentElement.querySelector('img').src
    const data = await fetch(src)
    const blob = await data.blob()

    await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
    e.target.textContent = 'Copied!'

  } else if (e.target.className == 'save') {
    const src = e.target.parentElement.parentElement.querySelector('img').src

    // Interesting trick
    const a = document.createElement('a');
    a.href = src;
    a.download = `image_${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    e.target.textContent = 'Saved!'
  }
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

function initializeProgress() {
  progressBar.style.backgroundColor = "#ff6a00"
  progressBar.textContent = "Processing..."
}

function setFinished() {
  progressBar.style.backgroundColor = "#006900"
  progressBar.textContent = "Done"
}

async function handleDrop(e) {
  const files = Array.from(e.dataTransfer.files);
  initializeProgress();
  await Promise.all(files.map(uploadAndPreviewFile));
  setFinished();
}

function previewFile(file) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const img = document.createElement('img')
      img.src = reader.result
      img.dataset.fileName = file.name

      // Add overlay buttons
      const container = document.createElement('div')
      container.className = 'image-container'
      container.appendChild(img)

      const buttonsDiv = document.createElement('div')
      buttonsDiv.className = 'overlay-buttons'

      const copyButton = document.createElement('div')
      copyButton.textContent = 'Copy'
      copyButton.className = 'copy'

      const saveButton = document.createElement('div')
      saveButton.textContent = 'Save'
      saveButton.className = 'save'

      buttonsDiv.appendChild(copyButton)
      buttonsDiv.appendChild(saveButton)
      container.appendChild(buttonsDiv)

      gallery.appendChild(container);
      resolve(file.name);
    };
    reader.readAsDataURL(file);
  });
}

async function uploadFile(file) {
  const url = 'upload';
  const base64String = await new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      resolve(reader.result.split(',')[1]);
    };
    reader.readAsDataURL(file);
  });

  const data = JSON.stringify({
    file: base64String,
    filename: file.name,
    content_type: file.type
  });

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: data
  });

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  return response.blob();
}

async function uploadAndPreviewFile(file) {
  try {
    await previewFile(file);
    const blob = await uploadFile(file);
    const imgURL = URL.createObjectURL(blob);
    const imgElement = document.querySelector(`img[data-file-name="${file.name}"]`);

    if (imgElement) {
      if (imgElement.dataset.src) {
        URL.revokeObjectURL(imgElement.dataset.src)
      }

      imgElement.src = imgURL; // Update the image source
    }
  } catch (error) {
    console.error("Something went wrong!", error);
  }
}