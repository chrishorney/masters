import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { LeaderboardPage } from './pages/LeaderboardPage'
import { TournamentLeaderboardPage } from './pages/TournamentLeaderboardPage'
import { EntryDetailPage } from './pages/EntryDetailPage'
import { AdminPage } from './pages/AdminPage'
import { RankingHistoryPage } from './pages/RankingHistoryPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/leaderboard" element={<LeaderboardPage />} />
            <Route path="/tournament-leaderboard" element={<TournamentLeaderboardPage />} />
            <Route path="/ranking-history" element={<RankingHistoryPage />} />
            <Route path="/entry/:entryId" element={<EntryDetailPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
