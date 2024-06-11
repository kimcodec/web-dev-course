function submitUserForm() {
    var name = document.getElementById('inputName').value;
    var max_price = document.getElementById('inputMaxPrice').value;
    var min_price = document.getElementById('inputMinPrice').value;

    window.location.href = '/?name=' + encodeURIComponent(name) + '&max_price=' +
        encodeURIComponent(max_price) + '&min_price=' + encodeURIComponent(min_price);
}

function submitAdminForm() {
    var name = document.getElementById('inputName').value;

    window.location.href = '/admin_panel/?name=' + encodeURIComponent(name);
}