'use strict';

function modalShown(event) {
    let button = event.relatedTarget;
    let furnitureID = button.dataset.furnitureId;
    let newUrl = `/cart/${furnitureID}/delete`;
    let form = document.getElementById('deleteFromCartModalForm');
    form.action = newUrl;
}

let modal = document.getElementById('deleteFromCartModal');
modal.addEventListener('show.bs.modal', modalShown);