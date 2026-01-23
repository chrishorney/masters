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
  const [activeTab, setActiveTab] = useState<'import' | 'bonus' | 'tournament'>('tournament')

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // If no tournament exists, show tournament management tab to create one
  if (error || !tournament) {
    // Still show the page, but default to tournament tab to allow creating one
    return (
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-gray-600">
            {!tournament 
              ? "No tournament found. Please create or sync a tournament to get started."
              : "Manage tournament data, imports, and bonus points"}
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-8" aria-label="Tabs">
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
            {tournament && (
              <>
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
              </>
            )}
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'tournament' && (
            <TournamentManagementSection tournament={tournament || undefined} />
          )}
          {activeTab === 'import' && tournament && (
            <ImportSection tournamentId={tournament.id} />
          )}
          {activeTab === 'bonus' && tournament && (
            <BonusPointsSection tournamentId={tournament.id} />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl md:text-4xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        {tournament && (
          <p className="text-gray-600 text-sm md:text-base">
            Managing: {tournament.name} • Round {tournament.current_round}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        {/* Desktop Tabs */}
        <nav className="hidden md:flex -mb-px space-x-8">
          <button
            onClick={() => setActiveTab('import')}
            className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
              activeTab === 'import'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            SmartSheet Imports
          </button>
          <button
            onClick={() => setActiveTab('bonus')}
            className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
              activeTab === 'bonus'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Bonus Points
          </button>
          <button
            onClick={() => setActiveTab('tournament')}
            className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
              activeTab === 'tournament'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Tournament Management
          </button>
        </nav>

        {/* Mobile Tabs - Dropdown */}
        <div className="md:hidden">
          <select
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value as 'import' | 'bonus' | 'tournament')}
            className="w-full py-3 px-4 border border-gray-300 rounded-lg bg-white text-gray-900 font-medium focus:ring-2 focus:ring-green-500 focus:border-green-500"
          >
            <option value="import">SmartSheet Imports</option>
            <option value="bonus">Bonus Points</option>
            <option value="tournament">Tournament Management</option>
          </select>
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'import' && tournament && (
          <ImportSection tournamentId={tournament.id} />
        )}
        {activeTab === 'import' && !tournament && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-yellow-800">
              Please create or sync a tournament first before importing entries.
            </p>
          </div>
        )}
        {activeTab === 'bonus' && tournament && (
          <BonusPointsSection tournamentId={tournament.id} />
        )}
        {activeTab === 'bonus' && !tournament && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-yellow-800">
              Please create or sync a tournament first before managing bonus points.
            </p>
          </div>
        )}
        {activeTab === 'tournament' && (
          <TournamentManagementSection tournament={tournament || undefined} />
        )}
      </div>
    </div>
  )
}
