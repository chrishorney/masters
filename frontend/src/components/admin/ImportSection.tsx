/** SmartSheet import section */
import { useState } from 'react'
import api from '../../services/api'

interface ImportSectionProps {
  tournamentId: number
}

export function ImportSection({ tournamentId }: ImportSectionProps) {
  const [importType, setImportType] = useState<'entries' | 'rebuys'>('entries')
  const [file, setFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setResult(null)
      setError(null)
    }
  }

  const handleImport = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    setImporting(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('tournament_id', tournamentId.toString())

      const endpoint = importType === 'entries' 
        ? '/admin/import/entries'
        : '/admin/import/rebuys'

      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Import failed. Please check the file format.')
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Import Type Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Import Type</h2>
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

      {/* File Upload */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          {importType === 'entries' ? 'Import Entries' : 'Import Rebuys'}
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select CSV File
            </label>
            <input
              type="file"
              accept=".csv"
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
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">Imported</div>
                  <div className="text-2xl font-bold text-gray-900">{result.imported || 0}</div>
                </div>
                <div>
                  <div className="text-gray-500">Skipped</div>
                  <div className="text-2xl font-bold text-gray-600">{result.skipped || 0}</div>
                </div>
                <div>
                  <div className="text-gray-500">Errors</div>
                  <div className="text-2xl font-bold text-red-600">{result.errors?.length || 0}</div>
                </div>
              </div>

              {result.errors && result.errors.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-medium text-gray-900 mb-2">Errors:</h4>
                  <div className="max-h-48 overflow-y-auto space-y-1">
                    {result.errors.map((err: any, idx: number) => (
                      <div key={idx} className="text-sm text-red-700 bg-red-50 p-2 rounded">
                        Row {err.row}: {err.error}
                        {err.participant && ` (${err.participant})`}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-red-600">
              <p>{result.error}</p>
            </div>
          )}
        </div>
      )}

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">CSV Format Requirements</h4>
        <div className="text-sm text-blue-800 space-y-1">
          {importType === 'entries' ? (
            <>
              <p><strong>Required columns:</strong> Participant Name, Player 1 Name, Player 2 Name, Player 3 Name, Player 4 Name, Player 5 Name, Player 6 Name</p>
              <p>See <code className="bg-blue-100 px-1 rounded">docs/examples/entries_example.csv</code> for format</p>
            </>
          ) : (
            <>
              <p><strong>Required columns:</strong> Participant Name, Original Player Name, Rebuy Player Name, Rebuy Type</p>
              <p>Rebuy Type must be: <code className="bg-blue-100 px-1 rounded">missed_cut</code> or <code className="bg-blue-100 px-1 rounded">underperformer</code></p>
              <p>See <code className="bg-blue-100 px-1 rounded">docs/examples/rebuys_example.csv</code> for format</p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
