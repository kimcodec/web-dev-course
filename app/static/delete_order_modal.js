'use strict';

function modalShown(event) {
    let button = event.relatedTarget;
    let orderId = button.dataset.orderId;
    let newUrl = `/orders/${orderId}/delete`;
    let form = document.getElementById('deleteOrderModalForm');
    form.action = newUrl;
}

let modal = document.getElementById('deleteOrderModal');
modal.addEventListener('show.bs.modal', modalShown);