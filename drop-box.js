const dropArea = document.getElementById("drop-area")
const gallery = document.getElementById('gallery')
const progressBar = document.getElementById('progress-bar')
const clearAllButton = document.getElementById('clear-all')
const saveAllButton = document.getElementById('save-all')

const HIGHLIGHT = 'highlight'
const dragEvents = ['dragenter', 'dragover', 'dragleave', 'drop']

// Class options for setting progress bar
const PROGRESS = 'progress'
const ERROR = 'error'
const DONE = 'done'

for (let eventName of dragEvents) {
  dropArea.addEventListener(eventName, preventDefaults, false)
  document.body.addEventListener(eventName, preventDefaults, false)
}

dropArea.addEventListener('dragenter', (e) => dropArea.classList.add(HIGHLIGHT))
dropArea.addEventListener('dragover', (e) => dropArea.classList.add(HIGHLIGHT))
dropArea.addEventListener('dragleave', (e) => dropArea.classList.remove(HIGHLIGHT))
dropArea.addEventListener('drop', (e) => dropArea.classList.remove(HIGHLIGHT))

dropArea.addEventListener('drop', handleDrop)
gallery.addEventListener('click', handleClick)
clearAllButton.addEventListener('click', clearAllImages)
saveAllButton.addEventListener('click', saveAllImages)

async function handleDrop(event) {
  const images = Array.from(event.dataTransfer.files)

  if (images.some(image => !image.type.startsWith('image'))) {
    setProgressBar(ERROR, 'Only Images Allowed')
    return
  }

  setProgressBar(PROGRESS, 'Processing...')
  await Promise.all(images.map(uploadAndPreviewFile))
  setProgressBar(DONE, 'Done')
}

function setProgressBar(className, text) {
  progressBar.className = className
  progressBar.textContent = text
}

async function uploadAndPreviewFile(file) {
    const [base64String, uuid] = await previewFile(file)
    await uploadFile(file, uuid, base64String)
}

function previewFile(file) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const uuid = window.crypto.randomUUID()
      gallery.appendChild(createImageElement(reader.result, uuid))
      resolve([reader.result.split(',')[1], uuid])
    }
    reader.readAsDataURL(file)
  })
}

async function uploadFile(file, uuid, base64String) {
  const url = 'upload'

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
  })

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  const blob = await response.blob()

  const reader = new FileReader()
  reader.onloadend = () => {
    const imgElement = document.querySelector(`img[data-file-name="${uuid}"]`)
    imgElement.src = reader.result
  }
  reader.readAsDataURL(blob)
}

function createImageElement(src, name) {
  const container = document.createElement('div')
  container.className = 'image-container'
  container.innerHTML = `<img src=${src} data-file-name=${name}>
                         <div class="overlay-buttons">
                            <div class="copy">Copy</div>
                            <div class="save">Save</div>
                         </div>`

  return container
}

function preventDefaults(event) {
  event.preventDefault()
  event.stopPropagation()
}

function clearAllImages(e) {
  gallery.innerHTML = ''
  setProgressBar('', 'Status')
}

async function handleClick(e) {
  const name = e.target.className

  if (name === 'copy' || name === 'save') {
    const img = e.target.closest('.image-container').querySelector('img')
    const blob = await (await fetch(img.src)).blob()

    if (name === 'copy') {
      await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
      e.target.textContent = 'Copied!'
    } else {
      saveImage(`image_${img.attributes['data-file-name'].nodeValue}.png`, blob)
      e.target.textContent = 'Saved!'
    }
  }
}

async function saveAllImages(e) {
  const images = gallery.querySelectorAll('img');

  if (images.length == 0) {
    setProgressBar(ERROR, 'No images to zip')
    return
  }

  setProgressBar(PROGRESS, 'Zipping images...')
  const zip = new JSZip()

  for (let image of images) {
    const blob = await (await fetch(image.src)).blob()
    const fileName = `image_${image.attributes['data-file-name'].nodeValue}.png`

    zip.file(fileName, blob)
  }

  const content = await zip.generateAsync({ type: 'blob' })
  saveImage('images.zip', content)
  setProgressBar(DONE, 'Downloaded zip')
}

function saveImage(url, content) {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(content)
    a.download = url
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(a.href)
}