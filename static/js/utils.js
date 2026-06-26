export function utilsData() {
  return {
    formatDate(iso) {
      if (!iso) return ''
      return new Date(iso).toLocaleString()
    },
  }
}
