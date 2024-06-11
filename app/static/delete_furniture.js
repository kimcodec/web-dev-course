'use strict';

function modalShown(event) {
    let button = event.relatedTarget;
    let furnitureID = button.dataset.furnitureId;
    let newUrl = `/furniture/${furnitureID}/delete`;
    let form = document.getElementById('deleteFurnitureModalForm');
    form.action = newUrl;
}

let modal = document.getElementById('deleteFurnitureModal');
modal.addEventListener('show.bs.modal', modalShown);