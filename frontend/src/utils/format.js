export function formatTime(val) {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  const offset = 16 * 60
  const local = new Date(d.getTime() + offset * 60 * 1000)
  const Y = local.getUTCFullYear()
  const M = String(local.getUTCMonth() + 1).padStart(2, '0')
  const D = String(local.getUTCDate()).padStart(2, '0')
  const h = String(local.getUTCHours()).padStart(2, '0')
  const m = String(local.getUTCMinutes()).padStart(2, '0')
  const s = String(local.getUTCSeconds()).padStart(2, '0')
  return `${Y}-${M}-${D} ${h}:${m}:${s}`
}
