/** Position over time chart component */
import { useMemo } from 'react'
import type { RankingSnapshot } from '../../types'

interface PositionChartProps {
  snapshots: RankingSnapshot[]
  entryNames?: Record<number, string>
}

export function PositionChart({ snapshots, entryNames }: PositionChartProps) {
  // Group snapshots by entry
  const entryData = useMemo(() => {
    const grouped: Record<number, RankingSnapshot[]> = {}
    
    snapshots.forEach(snapshot => {
      if (!grouped[snapshot.entry_id]) {
        grouped[snapshot.entry_id] = []
      }
      grouped[snapshot.entry_id].push(snapshot)
    })
    
    return Object.entries(grouped).map(([entryId, snaps]) => ({
      entryId: parseInt(entryId),
      entryName: entryNames?.[parseInt(entryId)] || `Entry ${entryId}`,
      snapshots: snaps.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    }))
  }, [snapshots, entryNames])

  // Calculate chart dimensions
  const maxPosition = Math.max(...snapshots.map(s => s.position), 1)
  const minTimestamp = Math.min(...snapshots.map(s => new Date(s.timestamp).getTime()))
  const maxTimestamp = Math.max(...snapshots.map(s => new Date(s.timestamp).getTime()))
  const timeRange = maxTimestamp - minTimestamp || 1

  // Generate colors for each entry
  const colors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#84CC16', '#F97316', '#6366F1'
  ]

  return (
    <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
      <h3 className="text-lg md:text-xl font-semibold text-gray-900 mb-4">Position Over Time</h3>
      
      <div className="relative" style={{ height: '400px', minHeight: '300px' }}>
        <svg 
          viewBox="0 0 800 400" 
          className="w-full h-full"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Grid lines */}
          {[1, 2, 3, 4, 5, 10, 15, 20].filter(p => p <= maxPosition).map(position => (
            <line
              key={`grid-${position}`}
              x1="50"
              y1={350 - (position - 1) * (300 / maxPosition)}
              x2="750"
              y2={350 - (position - 1) * (300 / maxPosition)}
              stroke="#E5E7EB"
              strokeWidth="1"
              strokeDasharray="4 4"
            />
          ))}

          {/* Y-axis labels (positions) */}
          {[1, 5, 10, 15, 20].filter(p => p <= maxPosition).map(position => (
            <text
              key={`label-${position}`}
              x="45"
              y={355 - (position - 1) * (300 / maxPosition)}
              textAnchor="end"
              className="text-xs fill-gray-600"
            >
              {position}
            </text>
          ))}

          {/* Plot lines for each entry */}
          {entryData.slice(0, 10).map((entry, idx) => {
            const color = colors[idx % colors.length]
            const points = entry.snapshots.map(snapshot => {
              const x = 50 + ((new Date(snapshot.timestamp).getTime() - minTimestamp) / timeRange) * 700
              const y = 350 - (snapshot.position - 1) * (300 / maxPosition)
              return `${x},${y}`
            }).join(' ')

            return (
              <g key={entry.entryId}>
                <polyline
                  points={points}
                  fill="none"
                  stroke={color}
                  strokeWidth="2"
                  opacity="0.7"
                />
                {/* Dots for each point */}
                {entry.snapshots.map(snapshot => {
                  const x = 50 + ((new Date(snapshot.timestamp).getTime() - minTimestamp) / timeRange) * 700
                  const y = 350 - (snapshot.position - 1) * (300 / maxPosition)
                  return (
                    <circle
                      key={snapshot.id}
                      cx={x}
                      cy={y}
                      r="4"
                      fill={color}
                    />
                  )
                })}
              </g>
            )
          })}

          {/* Axes */}
          <line x1="50" y1="50" x2="50" y2="350" stroke="#374151" strokeWidth="2" />
          <line x1="50" y1="350" x2="750" y2="350" stroke="#374151" strokeWidth="2" />

          {/* Axis labels */}
          <text x="400" y="390" textAnchor="middle" className="text-sm fill-gray-700 font-medium">
            Time
          </text>
          <text x="15" y="200" textAnchor="middle" className="text-sm fill-gray-700 font-medium" transform="rotate(-90 15 200)">
            Position
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        {entryData.slice(0, 10).map((entry, idx) => (
          <div key={entry.entryId} className="flex items-center gap-2">
            <div 
              className="w-4 h-4 rounded"
              style={{ backgroundColor: colors[idx % colors.length] }}
            />
            <span className="text-gray-700">{entry.entryName}</span>
          </div>
        ))}
      </div>

      {entryData.length > 10 && (
        <p className="text-xs text-gray-500 mt-2">
          Showing top 10 entries. {entryData.length - 10} more entries available.
        </p>
      )}
    </div>
  )
}
