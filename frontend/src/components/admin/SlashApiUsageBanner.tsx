import { useCallback, useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type SlashUsage = {
  year: number
  month: number
  timezone: string
  total_requests: number
  by_endpoint: Record<string, number>
  monthly_limit: number | null
  percent_of_limit: number | null
}

const MONTH_NAMES = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
]

export function SlashApiUsageBanner() {
  const [data, setData] = useState<SlashUsage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/admin/slash-api-usage`)
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }
      const json = (await res.json()) as SlashUsage
      setData(json)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load usage')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const label = data
    ? `${MONTH_NAMES[data.month - 1] ?? data.month} ${data.year} (${data.timezone})`
    : ''

  const endpoints = data
    ? Object.entries(data.by_endpoint).sort((a, b) => b[1] - a[1])
    : []

  return (
    <div className="mb-6 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-800 shadow-sm">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold text-slate-900">Slash Golf API usage</h2>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded border border-slate-300 bg-white px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
        >
          Refresh
        </button>
      </div>
      <p className="mb-3 text-xs text-slate-600">
        Counts successful calls only. Resets on the 1st of each calendar month ({label}).
      </p>

      {loading && <p className="text-slate-500">Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && data && (
        <>
          <div className="mb-3 flex flex-wrap items-baseline gap-2">
            <span className="text-2xl font-bold tabular-nums">{data.total_requests.toLocaleString()}</span>
            <span className="text-slate-600">requests this month</span>
            {data.monthly_limit != null && data.monthly_limit > 0 && (
              <span className="text-slate-500">
                / {data.monthly_limit.toLocaleString()} cap
              </span>
            )}
          </div>

          {data.monthly_limit != null && data.monthly_limit > 0 && data.percent_of_limit != null && (
            <div className="mb-3">
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full transition-all ${
                    data.percent_of_limit >= 100
                      ? 'bg-red-600'
                      : data.percent_of_limit >= 90
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                  }`}
                  style={{ width: `${Math.min(100, data.percent_of_limit)}%` }}
                />
              </div>
              <p className="mt-1 text-xs text-slate-600">{data.percent_of_limit}% of monthly cap</p>
            </div>
          )}

          {endpoints.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                By endpoint
              </p>
              <ul className="grid gap-1 sm:grid-cols-2">
                {endpoints.map(([name, count]) => (
                  <li key={name} className="flex justify-between gap-4 text-xs">
                    <span className="font-mono text-slate-700">{name}</span>
                    <span className="tabular-nums text-slate-600">{count.toLocaleString()}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}
