/**
 * CSV export utility
 */

/**
 * Export data as a CSV file with proper escaping and BOM for Excel compatibility
 * @param filename - The name of the file to download
 * @param headers - Array of column headers
 * @param rows - 2D array of data rows
 */
export function exportCSV(filename: string, headers: string[], rows: unknown[][]): void {
  const escape = (value: unknown): string => {
    const raw = String(value ?? '')
    // Prevent CSV injection by prefixing potentially dangerous values
    const safe = /^[=+@\-\t\r]/.test(raw) ? `'${raw}` : raw
    // Escape quotes by doubling them
    return `"${safe.replace(/"/g, '""')}"`
  }

  const csv = [headers, ...rows].map((row) => row.map(escape).join(',')).join('\r\n')

  // Create a blob with BOM for proper Excel UTF-8 handling
  const url = URL.createObjectURL(
    new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' }),
  )

  // Create and trigger download
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()

  // Clean up the object URL after a delay
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
