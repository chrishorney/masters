/** Main layout component with navigation */
import { Link, useLocation } from 'react-router-dom'
import { useCurrentTournament } from '../hooks/useTournament'

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const { data: tournament } = useCurrentTournament()

  const isActive = (path: string) => location.pathname === path

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-green-200">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="flex items-center space-x-2">
                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">🏌️</span>
                </div>
                <span className="text-xl font-bold text-gray-900">
                  Eldorado Masters Pool
                </span>
              </Link>
              
              <nav className="hidden md:flex space-x-1">
                <Link
                  to="/"
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    isActive('/')
                      ? 'bg-green-100 text-green-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Home
                </Link>
                <Link
                  to="/leaderboard"
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    isActive('/leaderboard')
                      ? 'bg-green-100 text-green-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Leaderboard
                </Link>
              </nav>
            </div>

            {/* Tournament Status */}
            {tournament && (
              <div className="hidden md:flex items-center space-x-4 text-sm">
                <div className="text-right">
                  <div className="font-medium text-gray-900">{tournament.name}</div>
                  <div className="text-gray-500">
                    Round {tournament.current_round} • {tournament.status}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>13th Annual Eldorado Masters Pool</p>
            <p className="mt-1">© {new Date().getFullYear()}</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
