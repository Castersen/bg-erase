const dropArea = document.getElementById("drop-area")
const gallery = document.getElementById('gallery')
const progressBar = document.getElementById('progress-bar')
const clearAllButton = document.getElementById('clear-all')
const saveAllButton = document.getElementById('save-all')

const HIGHLIGHT = 'highlight'
const dragEvents = ['dragenter', 'dragover', 'dragleave', 'drop']

for (let eventName of dragEvents) {
  dropArea.addEventListener(eventName, preventDefaults, false)
  document.body.addEventListener(eventName, preventDefaults, false)
}

dropArea.addEventListener('dragenter', () => dropArea.classList.add(HIGHLIGHT))
dropArea.addEventListener('dragover', () => dropArea.classList.add(HIGHLIGHT))
dropArea.addEventListener('dragleave', () => dropArea.classList.remove(HIGHLIGHT))
dropArea.addEventListener('drop', () => dropArea.classList.remove(HIGHLIGHT))

dropArea.addEventListener('drop', handleDrop)
gallery.addEventListener('click', handleClick)
clearAllButton.addEventListener('click', clearAllImages)
saveAllButton.addEventListener('click', saveAllImages)

async function handleDrop(event) {
  const images = Array.from(event.dataTransfer.files)

  if (images.some(image => !image.type.startsWith('image'))) {
    setProgressBar('error', 'Only Images Allowed')
    return
  }

  setProgressBar('progress', 'Processing...')
  await Promise.all(images.map(uploadAndPreviewFile))
  setProgressBar('done', 'Done')
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

function clearAllImages() {
  gallery.innerHTML = '';
  setProgressBar('', 'Status')
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

async function saveAllImages(e) {
  const images = gallery.querySelectorAll('img');

  if (images.length == 0) {
    setProgressBar('error', 'No images to zip')
    return
  }

  const zip = new JSZip()

  for (let image of images) {
    const response = await fetch(image.src)
    const blob = await response.blob()
    const fileName = `image_${image.attributes['data-file-name'].nodeValue}.png`

    zip.file(fileName, blob)
  }

  zip.generateAsync({ type: 'blob' })
    .then((content) => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(content)
      a.download = 'images.zip'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)

      URL.revokeObjectURL(a.href)
    });
}