function showDeleteModal(itemId) {
    // Set nilai ID data yang akan dihapus ke atribut "data-id" pada tombol "Hapus"
    document.getElementById('deleteButton').setAttribute('data-id', itemId);
    // Tampilkan modal konfirmasi penghapusan
    $('#deleteModal').modal('show');
}
