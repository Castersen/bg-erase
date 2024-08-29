const dropArea = document.getElementById("drop-area")
const gallery = document.getElementById('gallery')
const progressBar = document.getElementById('progress-bar')
const clearAllButton = document.getElementById('clear-all')

const HIGHLIGHT = 'highlight'
const dragEvents = ['dragenter', 'dragover', 'dragleave', 'drop']

for (let eventName of dragEvents) {
  dropArea.addEventListener(eventName, preventDefaults, false)
  document.body.addEventListener(eventName, preventDefaults, false)

  if (eventName == 'dragenter' || eventName == 'dragover')
    dropArea.addEventListener(eventName, () => {dropArea.classList.add(HIGHLIGHT)})
  if (eventName == 'dragleave' || eventName == 'drop')
    dropArea.addEventListener(eventName, () => {dropArea.classList.remove(HIGHLIGHT)})
}

dropArea.addEventListener('drop', handleDrop)
gallery.addEventListener('click', handleClick)
clearAllButton.addEventListener('click', clearAllImages)

async function handleDrop(event) {
  const images = Array.from(event.dataTransfer.files)

  for (let image of images) {
    if (!image.type.startsWith('image')) {
      setProgressBar('error', 'Only Images Allowed')
      return
    }
  }
  setProgressBar('progress', 'Processing...')
  await Promise.all(images.map(uploadAndPreviewFile))
  setProgressBar('done', 'Done')
}

function setProgressBar(className, text) {
  progressBar.classList = []
  progressBar.classList.add(className)
  progressBar.textContent = text
}

async function uploadAndPreviewFile(file) {
    const uuid = await previewFile(file)
    const blob = await uploadFile(file)
    const imgURL = URL.createObjectURL(blob)
    const imgElement = document.querySelector(`img[data-file-name="${uuid}"]`)
    imgElement.src = imgURL
}

function previewFile(file) {
  return new Promise((resolve) => {
    const reader = new FileReader()

    reader.onloadend = () => {
      const uuid = window.crypto.randomUUID()
      gallery.appendChild(createImageElement(reader.result, uuid))
      resolve(uuid)
    }

    reader.readAsDataURL(file)
  })
}

async function uploadFile(file) {
  const url = 'upload'

  const base64String = await new Promise((resolve) => {
    const reader = new FileReader()

    reader.onloadend = () => {
      resolve(reader.result.split(',')[1])
    }

    reader.readAsDataURL(file)
  })

  const data = JSON.stringify({
    file: base64String,
    filename: file.name,
    content_type: file.type
  })

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

function createImageElement(src, name) {
      const img = document.createElement('img')
      img.src = src
      img.dataset.fileName = name

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

      return container
}

function preventDefaults(event) {
  event.preventDefault()
  event.stopPropagation()
}

function clearAllImages() {
  const images = gallery.querySelectorAll('img')

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