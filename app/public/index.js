document.querySelectorAll(".drop-zone-input").forEach(inputElement => {
    const dropZoneElement = inputElement.closest(".drop-zone");

    dropZoneElement.addEventListener("click", e => {
        inputElement.click();
    })

    inputElement.addEventListener("change", e => {
        if (inputElement.files.length > 0){
            updateThumbnail(dropZoneElement, inputElement.files[0]);
        }
    })

    dropZoneElement.addEventListener("dragover", e => {
        e.preventDefault();
        dropZoneElement.classList.add("drop-zone-over");
    })

    dropZoneElement.addEventListener("dragleave", e => {
            e.preventDefault();
            dropZoneElement.classList.remove("drop-zone-over");
    });

    dropZoneElement.addEventListener("dragend", e => {
            e.preventDefault();
            dropZoneElement.classList.remove("drop-zone-over");
    });
    
    dropZoneElement.addEventListener("drop", e => {
        e.preventDefault();

        if (e.dataTransfer.files.length) {
            inputElement.files = e.dataTransfer.files;
            updateThumbnail(dropZoneElement, e.dataTransfer.files[0]);
        }

        dropZoneElement.classList.remove("drop-zone-over");
    });
});

/**
 * @param {HTMLElement} dropZoneElement 
 * @param {File} file 
 */
function updateThumbnail(dropZoneElement, file) {
    let thumbnailElement = dropZoneElement.querySelector(".drop-zone-thumb");
    const dropZonePrompt = dropZoneElement.querySelector(".drop-zone-prompt");

    if (file.type.startsWith("image/")){
        if (dropZonePrompt) dropZonePrompt.classList.add("hidden");

        if (!thumbnailElement){
            thumbnailElement = document.createElement("div");
            thumbnailElement.classList.add("drop-zone-thumb");
            dropZoneElement.appendChild(thumbnailElement);
        }

        thumbnailElement.dataset.label = file.name;

        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            thumbnailElement.style.backgroundImage = `url('${reader.result}')`;
        }
    }
    else{
        dropZonePrompt.classList.remove("hidden");
        dropZonePrompt.textContent = "Please select an image."

        if (thumbnailElement) thumbnailElement.style.backgroundImage = null;
    }
    
}