/** Manual entry roster management (add entries, edit slots, remove golfers). */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { adminApi } from '../../services/api'
import { LoadingSpinner } from '../LoadingSpinner'

type TournamentPlayer = {
  player_id: string
  full_name: string
  first_name?: string
  last_name?: string
}

type EntryRow = {
  id: number
  participant_id: number
  participant_name: string
  participant_email: string | null
  tournament_id: number
  player1_id: string | null
  player2_id: string | null
  player3_id: string | null
  player4_id: string | null
  player5_id: string | null
  player6_id: string | null
  rebuy_player_ids: string[]
  rebuy_original_player_ids: string[]
}

function SlotSelect({
  players,
  value,
  disabled,
  onPick,
}: {
  players: TournamentPlayer[]
  value: string | null
  disabled?: boolean
  onPick: (playerId: string | null) => void
}) {
  const [filter, setFilter] = useState('')
  const filtered = useMemo(() => {
    const f = filter.trim().toLowerCase()
    let list = players
    if (f) {
      list = players.filter(
        (p) =>
          (p.full_name || '').toLowerCase().includes(f) ||
          p.player_id.toLowerCase().includes(f)
      )
    }
    const slice = list.slice(0, 60)
    if (value && !slice.some((p) => p.player_id === value)) {
      const cur = players.find((p) => p.player_id === value)
      if (cur) slice.unshift(cur)
    }
    return slice
  }, [players, filter, value])

  return (
    <div className="flex flex-col gap-1 min-w-[10rem]">
      <input
        type="text"
        placeholder="Filter…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="text-xs border border-gray-200 rounded px-2 py-1"
        disabled={disabled}
      />
      <select
        className="text-sm border border-gray-300 rounded-lg px-2 py-1.5 bg-white"
        value={value || ''}
        disabled={disabled}
        onChange={(e) => {
          const v = e.target.value
          onPick(v === '' ? null : v)
        }}
      >
        <option value="">— Empty —</option>
        {filtered.map((p) => (
          <option key={p.player_id} value={p.player_id}>
            {p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim()}
          </option>
        ))}
      </select>
    </div>
  )
}

export function EntriesManagementSection({ tournamentId }: { tournamentId: number }) {
  const [entries, setEntries] = useState<EntryRow[]>([])
  const [players, setPlayers] = useState<TournamentPlayer[]>([])
  const [participantList, setParticipantList] = useState<
    Array<{ id: number; name: string; email: string | null; paid: boolean }>
  >([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  const [newMode, setNewMode] = useState<'new' | 'existing'>('new')
  const [newName, setNewName] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [existingParticipantId, setExistingParticipantId] = useState<number | ''>('')
  const [newSlots, setNewSlots] = useState<(string | null)[]>([null, null, null, null, null, null])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [eRes, pRes, partRes] = await Promise.all([
        adminApi.listEntries(tournamentId),
        adminApi.getTournamentPlayers(tournamentId),
        adminApi.listParticipants(),
      ])
      setEntries(eRes.entries)
      setPlayers(pRes.players || [])
      setParticipantList(partRes.participants || [])
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(ax.response?.data?.detail || ax.message || 'Failed to load entries')
    } finally {
      setLoading(false)
    }
  }, [tournamentId])

  useEffect(() => {
    load()
  }, [load])

  const nameById = useMemo(() => {
    const m = new Map<string, string>()
    for (const p of players) {
      m.set(
        p.player_id,
        p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim() || p.player_id
      )
    }
    return m
  }, [players])

  const handleRemovePlayer = async (entryId: number, playerId: string, label: string) => {
    if (
      !window.confirm(
        `Remove ${label} from this entry?\n\nThis deletes all points earned by that golfer for this entry only, then recalculates scores.`
      )
    ) {
      return
    }
    const key = `rm-${entryId}-${playerId}`
    setBusy(key)
    setError(null)
    try {
      await adminApi.removePlayerFromEntry(tournamentId, entryId, playerId)
      await load()
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(ax.response?.data?.detail || ax.message || 'Remove failed')
    } finally {
      setBusy(null)
    }
  }

  const handleSlotChange = async (entryId: number, slot: number, playerId: string | null) => {
    const key = `slot-${entryId}-${slot}`
    setBusy(key)
    setError(null)
    try {
      await adminApi.updateEntrySlot(tournamentId, entryId, slot, playerId)
      await load()
    } catch (e: unknown) {
      const ax = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(ax.response?.data?.detail || ax.message || 'Update failed')
    } finally {
      setBusy(null)
    }
  }

  const handleCreateEntry = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy('create')
    setError(null)
    try {
      const body: Parameters<typeof adminApi.createEntry>[1] = {
        player1_id: newSlots[0],
        player2_id: newSlots[1],
        player3_id: newSlots[2],
        player4_id: newSlots[3],
        player5_id: newSlots[4],
        player6_id: newSlots[5],
      }
      if (newMode === 'new') {
        if (!newName.trim()) {
          setError('Participant name is required')
          setBusy(null)
          return
        }
        body.participant = { name: newName.trim(), email: newEmail.trim() || null, paid: false }
      } else {
        if (!existingParticipantId) {
          setError('Select a participant')
          setBusy(null)
          return
        }
        body.participant_id = existingParticipantId as number
      }
      await adminApi.createEntry(tournamentId, body)
      setNewName('')
      setNewEmail('')
      setNewSlots([null, null, null, null, null, null])
      await load()
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } }; message?: string }
      setError(ax.response?.data?.detail || ax.message || 'Create failed')
    } finally {
      setBusy(null)
    }
  }

  if (loading && entries.length === 0) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-lg shadow border border-gray-100 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Add entry manually</h2>
        <p className="text-sm text-gray-600 mb-4">
          Pick a participant (new or existing), then assign golfers from the tournament field. At least one
          golfer is required. Empty slots are allowed after the migration; sync must have loaded players into
          the field so names appear in the dropdowns.
        </p>

        <form onSubmit={handleCreateEntry} className="space-y-4">
          <div className="flex flex-wrap gap-4 items-center">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                checked={newMode === 'new'}
                onChange={() => setNewMode('new')}
              />
              New participant
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                checked={newMode === 'existing'}
                onChange={() => setNewMode('existing')}
              />
              Existing participant
            </label>
          </div>

          {newMode === 'new' ? (
            <div className="grid md:grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                />
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Participant</label>
              <select
                className="w-full max-w-md border border-gray-300 rounded-lg px-3 py-2 bg-white"
                value={existingParticipantId === '' ? '' : String(existingParticipantId)}
                onChange={(e) =>
                  setExistingParticipantId(e.target.value ? Number(e.target.value) : '')
                }
              >
                <option value="">Select…</option>
                {participantList.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                    {p.email ? ` (${p.email})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <div key={i}>
                <div className="text-sm font-medium text-gray-700 mb-1">Player {i + 1}</div>
                <SlotSelect
                  players={players}
                  value={newSlots[i]}
                  disabled={busy === 'create'}
                  onPick={(pid) => {
                    const next = [...newSlots]
                    next[i] = pid
                    setNewSlots(next)
                  }}
                />
              </div>
            ))}
          </div>

          <button
            type="submit"
            disabled={busy === 'create'}
            className="bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
          >
            {busy === 'create' ? 'Creating…' : 'Create entry'}
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 text-sm">{error}</div>
      )}

      <div className="bg-white rounded-lg shadow border border-gray-100 overflow-x-auto">
        <h2 className="text-xl font-semibold text-gray-900 p-6 pb-2">Entries & rosters</h2>
        <p className="text-sm text-gray-600 px-6 pb-4">
          Remove a golfer to drop them from this team and strip all of their points for this entry (including
          manual GIR / fairways bonuses tied to that golfer). Rebuy pairs are cleared if that golfer appears in a
          rebuy mapping.
        </p>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 text-left">
              <th className="px-4 py-2 font-medium text-gray-700">Participant</th>
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <th key={n} className="px-2 py-2 font-medium text-gray-700 whitespace-nowrap">
                  P{n}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {entries.map((row) => (
              <tr key={row.id} className="border-b border-gray-100 align-top">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{row.participant_name}</div>
                  {row.participant_email && (
                    <div className="text-xs text-gray-500">{row.participant_email}</div>
                  )}
                </td>
                {[1, 2, 3, 4, 5, 6].map((slot) => {
                  const pid = row[`player${slot}_id` as keyof EntryRow] as string | null
                  const label = pid ? nameById.get(pid) || pid : '—'
                  return (
                    <td key={slot} className="px-2 py-2">
                      <div className="flex flex-col gap-1">
                        <SlotSelect
                          players={players}
                          value={pid}
                          disabled={busy !== null}
                          onPick={(next) => {
                            if (next !== pid) handleSlotChange(row.id, slot, next)
                          }}
                        />
                        {pid && (
                          <button
                            type="button"
                            className="text-xs text-red-600 hover:underline disabled:opacity-50"
                            disabled={busy !== null}
                            onClick={() =>
                              handleRemovePlayer(row.id, pid, label)
                            }
                          >
                            {busy === `rm-${row.id}-${pid}` ? 'Removing…' : 'Remove golfer'}
                          </button>
                        )}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
        {entries.length === 0 && (
          <p className="p-6 text-gray-500 text-sm">No entries yet. Import a sheet or add one above.</p>
        )}
      </div>

      <button
        type="button"
        onClick={() => load()}
        className="text-sm text-green-700 hover:underline"
        disabled={loading}
      >
        Refresh list
      </button>
    </div>
  )
}
