/** SmartSheet import section */
import { useState } from 'react'
import api from '../../services/api'
import { adminApi } from '../../services/api'

interface ImportSectionProps {
  tournamentId: number
}

export type SuggestionItem = { row: number; column: string; value: string; suggestion: string; player_id: string }
type TournamentPlayerOption = { player_id: string; name: string }
type PendingResolution = {
  row: number
  participant?: string
  column: string
  value: string
  suggested_player_id?: string
}

function formatImportError(err: any): string {
  if (!err) return 'Unknown import error'
  if (typeof err.error === 'string' && err.error.trim().length > 0) return err.error
  if (typeof err.message === 'string' && err.message.trim().length > 0) return err.message
  return 'Unknown import error'
}

function buildValidationRowErrors(rowResults: any[] | undefined): Array<{ row: number; participant?: string; error: string }> {
  if (!rowResults || rowResults.length === 0) return []
  const out: Array<{ row: number; participant?: string; error: string }> = []

  for (const row of rowResults) {
    if (!row?.row_error) continue
    const unresolvedPlayers = Array.isArray(row.players)
      ? row.players.filter((p: any) => p && !p.matched && !p.suggestion)
      : []

    if (unresolvedPlayers.length > 0) {
      const details = unresolvedPlayers
        .map((p: any) => `${p.column || 'Unknown column'} '${p.value || ''}'`)
        .join(', ')
      out.push({
        row: Number(row.row) || 0,
        participant: row.participant || undefined,
        error: `No match found for: ${details}`,
      })
      continue
    }

    out.push({
      row: Number(row.row) || 0,
      participant: row.participant || undefined,
      error: row.row_error,
    })
  }

  return out
}

export function ImportSection({ tournamentId }: ImportSectionProps) {
  const [importType, setImportType] = useState<'entries' | 'rebuys'>('entries')
  const [file, setFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [clearingEntries, setClearingEntries] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([])
  const [tournamentPlayerOptions, setTournamentPlayerOptions] = useState<TournamentPlayerOption[]>([])
  const [pendingResolutions, setPendingResolutions] = useState<PendingResolution[]>([])
  const [manualAssignments, setManualAssignments] = useState<Record<string, string>>({})

  const keyFor = (row: number, column: string) => `${row}::${column}`
  const clearMatchingState = () => {
    setSuggestions([])
    setTournamentPlayerOptions([])
    setPendingResolutions([])
    setManualAssignments({})
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setError(null)
      clearMatchingState()
    }
  }

  const runImport = async (appliedSuggestions?: Array<{ row: number; column: string; player_id: string }>) => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('tournament_id', tournamentId.toString())
    if (appliedSuggestions && appliedSuggestions.length > 0) {
      formData.append(
        'applied_suggestions',
        JSON.stringify(
          appliedSuggestions.map((s) => ({
            row: s.row,
            column: s.column,
            player_id: s.player_id,
          }))
        )
      )
    }
    const endpoint = importType === 'entries' ? '/admin/import/entries' : '/admin/import/rebuys'
    const response = await api.post(endpoint, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  const handleImport = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    setImporting(true)
    setError(null)
    setResult(null)
    clearMatchingState()

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('tournament_id', tournamentId.toString())

      if (importType === 'entries') {
        const validation = await adminApi.validateEntriesImport(formData)
        const allUnmatched = (validation.row_results || []).flatMap((r: any) => {
          if (!Array.isArray(r.players)) return []
          return r.players
            .filter((p: any) => p && !p.matched)
            .map((p: any) => ({
              row: Number(r.row) || 0,
              participant: r.participant || undefined,
              column: p.column,
              value: p.value || '',
              suggested_player_id: p.suggestion?.player_id,
            }))
        })
        if (validation.can_import_directly && allUnmatched.length === 0) {
          const data = await runImport()
          setResult(data)
        } else if (allUnmatched.length > 0) {
          const options = validation.tournament_player_options || []
          setTournamentPlayerOptions(options)
          setPendingResolutions(allUnmatched)
          const initialAssignments: Record<string, string> = {}
          for (const item of allUnmatched) {
            if (item.suggested_player_id) initialAssignments[keyFor(item.row, item.column)] = item.suggested_player_id
          }
          setManualAssignments(initialAssignments)
          // Keep old suggestion list for quick visual context
          setSuggestions(validation.suggestions || [])
        } else if (validation.error || (validation.row_results && validation.row_results.some((r: any) => r.row_error))) {
          const detailedErrors = buildValidationRowErrors(validation.row_results)
          setResult({
            success: false,
            error: validation.error || 'Some player names could not be matched. Fix the CSV or check for typos.',
            errors: detailedErrors,
          })
        } else {
          const data = await runImport()
          setResult(data)
        }
      } else {
        const validation = await adminApi.validateRebuysImport(formData)
        if (validation.can_import_directly && (!validation.suggestions || validation.suggestions.length === 0)) {
          const data = await runImport()
          setResult(data)
        } else if (validation.can_import_with_corrections && validation.suggestions && validation.suggestions.length > 0) {
          setSuggestions(validation.suggestions)
        } else if (validation.error || (validation.row_results && validation.row_results.some((r: any) => r.row_error))) {
          const detailedErrors = buildValidationRowErrors(validation.row_results)
          setResult({
            success: false,
            error: validation.error || 'Some player names could not be matched. Fix the CSV or check for typos.',
            errors: detailedErrors,
          })
        } else {
          const data = await runImport()
          setResult(data)
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Import failed. Please check the file format.')
    } finally {
      setImporting(false)
    }
  }

  const handleClearTournamentEntries = async () => {
    const ok = window.confirm(
      'This will wipe ALL entries for the current tournament (and remove calculated scores/bonus points/rankings), effectively clearing the leaderboard.\\n\\nThis cannot be undone. Are you sure you want to proceed?'
    )
    if (!ok) return

    setClearingEntries(true)
    setError(null)
    setResult(null)
    setSuggestions([])
    try {
      await adminApi.clearTournamentEntries(tournamentId, true)
      setResult({ success: true, message: 'Tournament entries cleared. You can import new entries now.' })
      // Reload so the current leaderboard/state re-fetches.
      window.location.reload()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to clear tournament entries')
    } finally {
      setClearingEntries(false)
    }
  }

  const handleApplySuggestionsAndImport = async () => {
    if (!file) return
    setImporting(true)
    setError(null)
    try {
      const assignments = pendingResolutions.map((p) => ({
        row: p.row,
        column: p.column,
        player_id: manualAssignments[keyFor(p.row, p.column)] || '',
      }))
      const missing = assignments.filter((a) => !a.player_id)
      if (missing.length > 0) {
        setImporting(false)
        setError(`Please choose a golfer for all unresolved names (${missing.length} remaining).`)
        return
      }
      const data = await runImport(assignments)
      setResult(data)
      clearMatchingState()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Import failed.')
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Import Type Selection */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">Import Type</h2>
        <div className="flex space-x-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="entries"
              checked={importType === 'entries'}
              onChange={(e) => setImportType(e.target.value as 'entries' | 'rebuys')}
              className="mr-2"
            />
            <span>Entries</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="rebuys"
              checked={importType === 'rebuys'}
              onChange={(e) => setImportType(e.target.value as 'entries' | 'rebuys')}
              className="mr-2"
            />
            <span>Rebuys</span>
          </label>
        </div>
      </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4 md:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-semibold text-red-900 mb-1">Clear current tournament entries</h3>
              <p className="text-sm text-red-800">
                Deletes the current tournament&apos;s entries and calculated leaderboard data. Use this only if you need to re-import.
              </p>
            </div>
            <button
              type="button"
              onClick={handleClearTournamentEntries}
              disabled={importing || clearingEntries}
              className="px-4 py-2 bg-red-700 text-white rounded-lg hover:bg-red-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {clearingEntries ? 'Clearing...' : 'Clear Entries'}
            </button>
          </div>
        </div>

      {/* File Upload */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <h2 className="text-xl md:text-2xl font-semibold text-gray-900 mb-4">
          {importType === 'entries' ? 'Import Entries' : 'Import Rebuys'}
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File (.csv or .xlsx)
            </label>
            <input
              type="file"
              accept=".csv,.xlsx,.xlsm"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
            />
            {file && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {file.name}
              </p>
            )}
          </div>

          <button
            onClick={handleImport}
            disabled={!file || importing}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {importing ? 'Importing...' : 'Import'}
          </button>
        </div>
      </div>

      {/* Spelling suggestions (entries and rebuys) */}
      {(pendingResolutions.length > 0 || suggestions.length > 0) && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 md:p-6">
          <h3 className="text-lg font-semibold text-amber-900 mb-2">Resolve unmatched names</h3>
          <p className="text-sm text-amber-800 mb-4">
            We found names that didn&apos;t match exactly. Review each row and choose the correct golfer.
          </p>
          {pendingResolutions.length > 0 ? (
            <div className="space-y-3 mb-4 max-h-72 overflow-y-auto">
              {pendingResolutions.map((r, idx) => {
                const k = keyFor(r.row, r.column)
                return (
                  <div key={`${k}-${idx}`} className="bg-white border border-amber-200 rounded p-3 text-sm">
                    <div className="text-amber-900 mb-2">
                      <span className="font-medium">Row {r.row}, {r.column}</span>
                      {r.participant ? ` (${r.participant})` : ''}: <span className="line-through">{r.value || '[blank]'}</span>
                    </div>
                    <select
                      value={manualAssignments[k] || ''}
                      onChange={(e) =>
                        setManualAssignments((prev) => ({
                          ...prev,
                          [k]: e.target.value,
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900"
                    >
                      <option value="">Select golfer...</option>
                      {tournamentPlayerOptions.map((opt) => (
                        <option key={opt.player_id} value={opt.player_id}>
                          {opt.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )
              })}
            </div>
          ) : (
            <ul className="space-y-2 mb-4 max-h-48 overflow-y-auto">
              {suggestions.map((s, idx) => (
                <li key={idx} className="text-sm text-amber-900 flex items-center gap-2">
                  <span className="font-medium">Row {s.row}, {s.column}:</span>
                  <span className="line-through">{s.value}</span>
                  <span>→</span>
                  <span className="font-semibold text-green-800">{s.suggestion}</span>
                </li>
              ))}
            </ul>
          )}
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleApplySuggestionsAndImport}
              disabled={importing}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              {importing ? 'Importing...' : 'Apply selections and import'}
            </button>
            <button
              type="button"
              onClick={clearMatchingState}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium mb-2">Error</h3>
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {result && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Import Results</h3>
          
          {result.success ? (
            <div className="space-y-3">
              <div className="flex items-center space-x-2 text-green-600">
                <span>✓</span>
                <span className="font-medium">Import Successful</span>
              </div>
              <div className="grid grid-cols-3 gap-2 md:gap-4 text-sm">
                <div>
                  <div className="text-gray-500 text-xs md:text-sm">Imported</div>
                  <div className="text-xl md:text-2xl font-bold text-gray-900">{result.imported || 0}</div>
                </div>
                <div>
                  <div className="text-gray-500 text-xs md:text-sm">Skipped</div>
                  <div className="text-xl md:text-2xl font-bold text-gray-600">{result.skipped || 0}</div>
                </div>
                <div>
                  <div className="text-gray-500 text-xs md:text-sm">Errors</div>
                  <div className="text-xl md:text-2xl font-bold text-red-600">{result.errors?.length || 0}</div>
                </div>
              </div>

            </div>
          ) : (
            <div className="text-red-600">
              <p>{result.error}</p>
            </div>
          )}

          {result.errors && result.errors.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 mb-2">Rows that could not be imported:</h4>
              <div className="max-h-64 overflow-y-auto space-y-1">
                {result.errors.map((rawErr: any, idx: number) => {
                  const err = {
                    row: Number(rawErr?.row) || 0,
                    participant: rawErr?.participant,
                    error: formatImportError(rawErr),
                  }
                  return (
                    <div key={idx} className="text-sm text-red-700 bg-red-50 p-2 rounded">
                      Row {err.row}: {err.error}
                      {err.participant && ` (${err.participant})`}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">File Format Requirements</h4>
        <div className="text-sm text-blue-800 space-y-1">
          {importType === 'entries' ? (
            <>
              <p><strong>Required columns:</strong> Participant Name, Player 1 Name, Player 2 Name, Player 3 Name, Player 4 Name, Player 5 Name, Player 6 Name</p>
              <p>Upload <code className="bg-blue-100 px-1 rounded">.csv</code> or <code className="bg-blue-100 px-1 rounded">.xlsx</code>. See <code className="bg-blue-100 px-1 rounded">docs/examples/entries_example.csv</code> for format.</p>
            </>
          ) : (
            <>
              <p><strong>Required columns (SmartSheet export):</strong> Player Name (or Participant Name), Professional 1-6, then Replace/Replace with pairs after Professional 6.</p>
              <p>No <code className="bg-blue-100 px-1 rounded">Rebuy Type</code> column is needed.</p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
