/** Admin dashboard page */
import { useState } from 'react'
import { useCurrentTournament } from '../hooks/useTournament'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { ImportSection } from '../components/admin/ImportSection'
import { BonusPointsSection } from '../components/admin/BonusPointsSection'
import { TournamentManagementSection } from '../components/admin/TournamentManagementSection'

export function AdminPage() {
  const { data: tournament, isLoading, error } = useCurrentTournament()
  const [activeTab, setActiveTab] = useState<'import' | 'bonus' | 'tournament'>('import')

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <ErrorMessage 
          message="Failed to load tournament information."
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        {tournament && (
          <p className="text-gray-600">
            Managing: {tournament.name} • Round {tournament.current_round}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('import')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'import'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            SmartSheet Imports
          </button>
          <button
            onClick={() => setActiveTab('bonus')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'bonus'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Bonus Points
          </button>
          <button
            onClick={() => setActiveTab('tournament')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'tournament'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Tournament Management
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'import' && tournament && (
          <ImportSection tournamentId={tournament.id} />
        )}
        {activeTab === 'bonus' && tournament && (
          <BonusPointsSection tournamentId={tournament.id} />
        )}
        {activeTab === 'tournament' && tournament && (
          <TournamentManagementSection tournament={tournament} />
        )}
      </div>
    </div>
  )
}
