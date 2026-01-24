/** Home page */
import { Link } from 'react-router-dom'
import { useCurrentTournament } from '../hooks/useTournament'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'

export function HomePage() {
  const { data: tournament, isLoading, error } = useCurrentTournament()

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <ErrorMessage 
          message="Failed to load tournament information. Please try again later."
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-4">
          Welcome to the 13th Annual
        </h1>
        <h2 className="text-2xl md:text-4xl font-bold text-green-600 mb-6">
          Eldorado Masters Pool
        </h2>
        {tournament && (
          <div className="inline-block bg-white rounded-lg shadow-md px-6 py-4 mb-8">
            <div className="text-2xl font-semibold text-gray-900 mb-2">
              {tournament.name}
            </div>
            <div className="text-gray-600">
              {new Date(tournament.start_date).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric',
                timeZone: 'America/Chicago'
              })}{' '}
              -{' '}
              {new Date(tournament.end_date).toLocaleDateString('en-US', {
                month: 'long',
                day: 'numeric',
                year: 'numeric',
                timeZone: 'America/Chicago'
              })}
            </div>
            <div className="mt-2 text-sm text-gray-500">
              Round {tournament.current_round} • {tournament.status}
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6 mb-12">
        <Link
          to="/leaderboard"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow group"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2 group-hover:text-green-600 transition-colors">
                View Leaderboard
              </h3>
              <p className="text-gray-600">
                See current standings and scores
              </p>
            </div>
            <div className="text-3xl group-hover:scale-110 transition-transform">
              📊
            </div>
          </div>
        </Link>

        {tournament && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Tournament Info
                </h3>
                <p className="text-gray-600">
                  {tournament.year} Masters Tournament
                </p>
              </div>
              <div className="text-3xl">🏆</div>
            </div>
          </div>
        )}
      </div>

      {/* Rules Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h3 className="text-2xl font-semibold text-gray-900 mb-4">
          How It Works
        </h3>
        <div className="space-y-3 text-gray-700">
          <p>
            Each participant selects 6 golfers. Points are awarded based on player
            performance throughout the tournament.
          </p>
          <p>
            <strong>Daily Points:</strong> Points are awarded based on position after
            each round (Leader, Top 5, Top 10, Top 25, Made Cut).
          </p>
          <p>
            <strong>Bonus Points:</strong> Additional points for GIR leader, Fairways
            leader, low score of day, eagles, double eagles, and hole-in-ones.
          </p>
          <p>
            <strong>Weekend Bonus:</strong> 5 bonus points if all 6 players make the cut.
          </p>
        </div>
      </div>
    </div>
  )
}
