let dropArea = document.getElementById("drop-area")

// Prevent default drag behaviors
;['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false)   
  document.body.addEventListener(eventName, preventDefaults, false)
})

// Highlight drop area when item is dragged over it
;['dragenter', 'dragover'].forEach(eventName => {
  dropArea.addEventListener(eventName, highlight, false)
})

;['dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, unhighlight, false)
})

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false)

function preventDefaults (e) {
  e.preventDefault()
  e.stopPropagation()
}

function highlight(e) {
  dropArea.classList.add('highlight')
}

function unhighlight(e) {
  dropArea.classList.remove('active')
}

function handleDrop(e) {
  var dt = e.dataTransfer
  var files = dt.files

  handleFiles(files)
}

let uploadProgress = []
let processingButton = document.getElementById('progress-bar')

function initializeProgress() {
  processingButton.textContent = "Processing..."
}

function setFinished() {
  processingButton.textContent = "Done"
}

function handleFiles(files) {
  files = [...files]
  initializeProgress(files.length)
  files.forEach(uploadFile)
  files.forEach(previewFile)
  setFinished()
}

function previewFile(file) {
  let reader = new FileReader()
  reader.readAsDataURL(file)
  reader.onloadend = function() {
    let img = document.createElement('img')
    img.src = reader.result
    document.getElementById('gallery').appendChild(img)
  }
}

function uploadFile(file, i) {
    var url = 'upload'
    var xhr = new XMLHttpRequest()
    var reader = new FileReader()

    reader.onloadend = function() {
        var base64String = reader.result.split(',')[1];

        var data = JSON.stringify({
            upload_preset: 'ujpu6gyk',
            file: base64String,
            filename: file.name,
            content_type: file.type
        });

        xhr.open('POST', url, true)
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest')

        xhr.responseType = 'blob'

        xhr.addEventListener('readystatechange', function(e) {
            if (xhr.readyState == 4 && xhr.status == 200) {
              var blob = xhr.response
              var imgURL = URL.createObjectURL(blob);
              var imgElement = document.createElement('img');
              imgElement.src = imgURL;
              document.getElementById('gallery').appendChild(imgElement);
            }
            else if (xhr.readyState == 4 && xhr.status != 200) {
              console.error("Something went wrong!")
            }
        })

        xhr.send(data)
    }

    reader.readAsDataURL(file);

}