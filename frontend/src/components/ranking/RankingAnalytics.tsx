/** Ranking analytics component */
import type { RankingAnalytics as RankingAnalyticsType } from '../../types'

interface RankingAnalyticsProps {
  analytics: RankingAnalyticsType
}

export function RankingAnalytics({ analytics }: RankingAnalyticsProps) {
  return (
    <div className="space-y-6">
      {/* Biggest Movers */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <h3 className="text-lg md:text-xl font-semibold text-gray-900 mb-4">Biggest Movers</h3>
        
        {analytics.biggest_movers.length === 0 ? (
          <p className="text-gray-500">No position changes recorded yet.</p>
        ) : (
          <div className="space-y-3">
            {analytics.biggest_movers.slice(0, 10).map((mover, idx) => (
              <div
                key={mover.entry_id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-semibold ${
                    mover.improvement 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {idx + 1}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{mover.entry_name}</div>
                    <div className="text-sm text-gray-600">
                      Position {mover.start_position} → {mover.end_position}
                    </div>
                  </div>
                </div>
                <div className={`font-semibold ${
                  mover.improvement ? 'text-green-600' : 'text-red-600'
                }`}>
                  {mover.improvement ? '+' : ''}{mover.position_change}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Position Distribution */}
      <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
        <h3 className="text-lg md:text-xl font-semibold text-gray-900 mb-4">Position Distribution</h3>
        
        <div className="space-y-2">
          {Object.values(analytics.position_distribution)
            .sort((a, b) => a.position - b.position)
            .slice(0, 10)
            .map(dist => (
              <div key={dist.position} className="flex items-center gap-4">
                <div className="w-16 text-sm font-medium text-gray-700">
                  #{dist.position}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-4">
                      <div
                        className="bg-green-600 h-4 rounded-full"
                        style={{ width: `${(dist.unique_entries_count / Math.max(...Object.values(analytics.position_distribution).map(d => d.unique_entries_count))) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600 w-20 text-right">
                      {dist.unique_entries_count} {dist.unique_entries_count === 1 ? 'entry' : 'entries'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Time in Lead */}
      {analytics.time_in_lead.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
          <h3 className="text-lg md:text-xl font-semibold text-gray-900 mb-4">Time in Lead</h3>
          
          <div className="space-y-3">
            {analytics.time_in_lead
              .sort((a, b) => b.seconds - a.seconds)
              .map((leader, idx) => (
                <div
                  key={leader.entry_id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center font-semibold">
                      {idx + 1}
                    </div>
                    <div className="font-medium text-gray-900">{leader.entry_name}</div>
                  </div>
                  <div className="font-semibold text-gray-700">{leader.formatted}</div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
