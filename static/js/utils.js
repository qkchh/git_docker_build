export function utilsData() {
  return {
    formatDate(iso) {
      if (!iso) return ''
      return new Date(iso).toLocaleString()
    },

    // ================================================================
    // Confirm dialog
    // ================================================================
    confirmModal: null,

    showConfirm(message, onConfirm) {
      this.confirmModal = { message, onConfirm }
    },

    confirmOk() {
      if (this.confirmModal?.onConfirm) this.confirmModal.onConfirm()
      this.confirmModal = null
    },

    confirmCancel() {
      this.confirmModal = null
    },

    // ================================================================
    // Toast notification
    // ================================================================
    toastMsg: '',
    _toastTimer: null,

    showToast(msg) {
      this.toastMsg = msg
      clearTimeout(this._toastTimer)
      this._toastTimer = setTimeout(() => { this.toastMsg = '' }, 4000)
    },
  }
}
