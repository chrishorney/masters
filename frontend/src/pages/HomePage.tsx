/** Home page */
import { Link } from 'react-router-dom'
import { useCurrentTournament } from '../hooks/useTournament'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { PushNotificationSettings } from '../components/PushNotificationSettings'
import { DiscordInvite } from '../components/DiscordInvite'

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

      {/* Discord Invite */}
      <div className="mb-8 flex justify-center">
        <DiscordInvite />
      </div>

      {/* Rules Section */}
      <div className="bg-white rounded-lg shadow-md p-6 md:p-8 mb-8">
        <h3 className="text-2xl md:text-3xl font-semibold text-gray-900 mb-6">
          Tournament Rules
        </h3>
        <div className="space-y-6 text-gray-700">
          {/* Rule 1 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">1. Talk to Brandon Nelson :)</h4>
          </div>

          {/* Rule 2 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">2. Player Selection</h4>
            <p className="text-gray-700">
              Pick any 6 players from the Masters field, submit your picks to the tournament chairman by Wednesday before the Masters, 7PM CST.
            </p>
          </div>

          {/* Rule 3 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">3. Scoring</h4>
            <p className="text-gray-700 mb-3">
              Points are awarded based on where your 6 selected players finish and perform during each tournament day. Any ties will result in both players receiving full point value (Example – if 4 players finish a day T4, all 4 will earn the point value for a top 5 daily finish)
            </p>
            
            <div className="bg-gray-50 rounded-lg p-4 mb-3">
              <h5 className="font-semibold text-gray-900 mb-2">Thursday scoring:</h5>
              <ul className="list-disc list-inside space-y-1 text-gray-700 ml-2">
                <li>Tournament Leader = 8 points</li>
                <li>Players in top 5 = 5 points</li>
                <li>Players in top 10 = 3 points</li>
                <li>Players in top 25 = 1 point</li>
              </ul>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 mb-3">
              <h5 className="font-semibold text-gray-900 mb-2">Friday & Saturday scoring:</h5>
              <ul className="list-disc list-inside space-y-1 text-gray-700 ml-2">
                <li>Tournament leader = 12 points</li>
                <li>Players in top 5 = 8 points</li>
                <li>Players in top 10 = 5 points</li>
                <li>Players in top 25 = 3 points</li>
                <li>Make cut, outside top 25 = 1 pt.</li>
              </ul>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-900 mb-2">Sunday Scoring:</h5>
              <p className="text-gray-700 mb-2">Same as Friday and Saturday scoring except for tournament winner earns 15 points</p>
            </div>
          </div>

          {/* Rule 4 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">4. Bonus Points</h4>
            <p className="text-gray-700 mb-3">
              Additional "Bonus" points will be awarded on all four tournament days. Bonus points will be given to players who:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 ml-4">
              <li>Leads the field each day in greens in regulation (per day) = 1 point.</li>
              <li>Leads the field each day in fairways hit (per day) = 1 point.</li>
              <li>Low score of the day (per day) = 1 point</li>
              <li>Eagles (per day) = 2 points (hole in one, see below)</li>
              <li>Double Eagle = 3 points</li>
              <li>Hole in one bonus = 3 points (eagle / 2 pts + 1)</li>
              <li>If your six chosen golfers make the weekend = 5 points. (forfeited if rebuy)</li>
            </ul>
          </div>

          {/* Rule 5 */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-2">5. Re-buy</h4>
            <p className="text-gray-700 mb-3">
              There are two player re-buy scenarios:
            </p>
            
            <div className="bg-blue-50 rounded-lg p-4 mb-3">
              <h5 className="font-semibold text-gray-900 mb-2">a. Missed Cut Re-buy:</h5>
              <p className="text-gray-700">
                If a chosen player does not make the cut you may buy replacement players after play concludes on Friday. The re-buy player's earned points (including bonus points) will be awarded from play on Saturday and Sunday only. If your original player that missed the cut earned points (example, bonus points, inside the top 25 for Thursday, etc) those points will remain toward your total score.
              </p>
            </div>

            <div className="bg-blue-50 rounded-lg p-4">
              <h5 className="font-semibold text-gray-900 mb-2">b. Under Performer Re-buy:</h5>
              <p className="text-gray-700">
                If you have chosen an "under performer" you may re-buy replacement players after play concludes on Friday. An under performer's earned points will remain (Thursday and Friday only), however you forfeit your 5 bonus points for all six chosen golfers making it to the weekend. The re-buy player's earned points (including bonus points) will be awarded from play on Saturday and Sunday only. Your Re-buy player(s) must be communicated to the tournament chairman BEFORE play begins on Saturday.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Push Notification Settings */}
      <div className="mt-8">
        <PushNotificationSettings />
      </div>
    </div>
  )
}
