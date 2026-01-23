# Future Improvements & Feature Roadmap

This document outlines potential improvements and features for future development phases. These are not immediate priorities but represent opportunities to enhance the application.

## Phase 11: User Authentication & Access Control

### Features
- **User Registration/Login**
  - JWT-based authentication
  - User accounts for participants
  - Password reset functionality
  - Email verification

- **Role-Based Access Control**
  - Admin role (full access)
  - Participant role (view own entry only)
  - Public role (view leaderboard only)

- **Entry Ownership**
  - Participants can view/edit their own entries
  - Prevent unauthorized access to entry details
  - Secure admin endpoints

### Benefits
- Better security
- Personalized experience
- Ability to let participants manage their own entries

---

## Phase 12: Ranking History & Position Tracking ✅ **IMPLEMENTED**

### Status
**Completed**: This feature has been fully implemented and is now in production.

### Features ✅
- **Ranking History Database**
  - New `ranking_snapshots` table to track entry positions over time
  - Capture ranking after each score calculation
  - Store: entry_id, tournament_id, round_id, position, total_points, timestamp
  - Index on (tournament_id, timestamp) for fast queries

- **Automatic Position Tracking**
  - Hook into score calculation process
  - After scores are calculated, determine rankings
  - Save snapshot of all entry positions
  - Track both position (1st, 2nd, etc.) and points at that moment

- **Visualization Dashboard** ✅
  - **Position Over Time Chart** ✅
    - Line chart showing each entry's position throughout tournament ✅
    - X-axis: Time/Round progression ✅
    - Y-axis: Position (inverted - lower is better) ✅
    - Color-coded lines for each entry ✅
    - Interactive tooltips showing points at each snapshot ✅
  
  - **Position Heatmap** ⏳ (Future Enhancement)
    - Grid showing position changes round-by-round
    - Rows: Entries (sorted by final position)
    - Columns: Rounds
    - Color intensity: Position (darker = better position)
    - Quick visual of who moved up/down each round
  
  - **Biggest Movers** ✅
    - Show entries with largest position changes ✅
    - "Biggest Climb" (e.g., 15th → 3rd) ✅
    - "Biggest Drop" (e.g., 2nd → 12th) ✅
    - Highlight dramatic position swings ✅
  
  - **Position Distribution** ✅
    - Bar chart showing how many entries held each position ✅
    - "How many different entries were in 1st place?" ✅
    - Shows competitiveness of tournament ✅

- **Additional Analytics**
  - **Time in Lead** ✅
    - Track how long each entry held 1st place ✅
    - "Leaderboard dominance" metric ✅
  
  - **Consistency Score** ⏳ (Future Enhancement)
    - Measure how stable each entry's position was
    - Low variance = consistent performance
    - High variance = volatile (big swings)
  
  - **Round-by-Round Performance** ⏳ (Future Enhancement)
    - Show which rounds each entry gained/lost the most positions
    - Identify "clutch rounds" where someone made a big move
  
  - **Projected Finish** ⏳ (Future Enhancement)
    - Based on current trajectory, predict final position
    - Show confidence intervals
    - "If trends continue, Entry X will finish in Y position"

### Database Schema

```python
class RankingSnapshot(Base):
    __tablename__ = "ranking_snapshots"
    
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=False)
    round_id = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)  # 1st, 2nd, 3rd, etc.
    total_points = Column(Float, nullable=False)
    points_behind_leader = Column(Float)  # How many points behind 1st place
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_tournament_timestamp', 'tournament_id', 'timestamp'),
        Index('idx_entry_tournament', 'entry_id', 'tournament_id'),
    )
```

### Implementation Approach ✅

1. **Create Migration** ✅
   - Add `ranking_snapshots` table ✅
   - Add indexes for performance ✅

2. **Modify Score Calculator** ✅
   - After calculating all scores, determine rankings ✅
   - Create snapshot records for all entries ✅
   - Hook into `calculate_scores_for_tournament` method ✅

3. **API Endpoints** ✅
   - `GET /api/ranking-history/tournament/{id}` - Get all snapshots ✅
   - `GET /api/ranking-history/entry/{id}` - Get position over time for one entry ✅
   - `GET /api/ranking-history/analytics/{id}` - Get analytics (biggest movers, etc.) ✅

4. **Frontend Components** ✅
   - `PositionChart.tsx` - SVG line chart component ✅
   - `RankingAnalytics.tsx` - Analytics dashboard ✅
   - `RankingHistoryPage.tsx` - Full page with filters and visualizations ✅
   - Mobile-responsive design ✅

### Benefits
- **Engagement**: Users can see their journey through the tournament
- **Competitiveness**: Visualize how close the competition is
- **Storytelling**: "Look how Entry X climbed from 20th to 1st!"
- **Analytics**: Understand tournament dynamics and patterns
- **Historical Data**: Track trends across multiple tournaments

### Technical Considerations
- **Performance**: Indexing is critical for fast queries
- **Storage**: May accumulate significant data over time (consider archiving old tournaments)
- **Real-time**: Could update visualizations as new snapshots are created
- **Caching**: Cache analytics calculations for frequently viewed tournaments

---

## Phase 13: Real-Time Updates (Server-Sent Events / WebSockets)

### Status
**Recommended Approach**: Start with Server-Sent Events (SSE) - simpler implementation that fits the use case perfectly.

### Why Real-Time Updates?

**Current Limitations**:
- Frontend polls every 30 seconds (`refetchInterval: 30 * 1000`)
- Users see updates up to 30 seconds after scores are calculated
- Wasted API calls: 10 users = 20 requests/minute, even when nothing changed
- Doesn't scale well: 100 users = 200 requests/minute

**Benefits of Real-Time**:
- ⚡ **Instant Updates**: < 1 second delay vs 0-30 second delay
- 📉 **Reduced Server Load**: 99% reduction in unnecessary requests
- 🔋 **Battery Efficient**: One connection vs constant polling
- 👥 **Synchronized**: All users see updates simultaneously
- 🎯 **Better UX**: More engaging, "live" feel

### Recommended: Server-Sent Events (SSE)

**Why SSE Over WebSockets?**
- ✅ Simpler to implement (~1 day vs 2-3 days)
- ✅ Perfect for one-way updates (server → client)
- ✅ Built into browsers, automatic reconnection
- ✅ Easier to debug and maintain
- ✅ Can upgrade to WebSockets later if needed

### Implementation Plan

#### Backend Implementation

1. **SSE Endpoint**
   ```python
   @router.get("/scores/stream/{tournament_id}")
   async def stream_score_updates(
       tournament_id: int,
       db: Session = Depends(get_db)
   ):
       """Stream score updates via Server-Sent Events."""
       async def event_generator():
           # Send initial state
           yield f"data: {json.dumps({'type': 'connected'})}\n\n"
           
           # Watch for score changes
           last_snapshot_id = None
           while True:
               # Check for new score calculations
               latest_snapshot = db.query(ScoreSnapshot).filter(
                   ScoreSnapshot.tournament_id == tournament_id
               ).order_by(ScoreSnapshot.timestamp.desc()).first()
               
               if latest_snapshot and latest_snapshot.id != last_snapshot_id:
                   # New scores calculated, send update
                   leaderboard = get_leaderboard_data(tournament_id)
                   yield f"data: {json.dumps({
                       'type': 'scores_updated',
                       'data': leaderboard
                   })}\n\n"
                   last_snapshot_id = latest_snapshot.id
               
               await asyncio.sleep(2)  # Check every 2 seconds
       
       return StreamingResponse(
           event_generator(),
           media_type="text/event-stream",
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
           }
       )
   ```

2. **Integration Points**
   - Hook into `calculate_scores_for_tournament` completion
   - Trigger SSE broadcast when scores are calculated
   - Use Redis pub/sub for multi-server deployments (optional)

3. **Connection Management**
   - Track active connections
   - Handle disconnections gracefully
   - Heartbeat messages to keep connection alive
   - Automatic reconnection on client side

#### Frontend Implementation

1. **SSE Hook**
   ```typescript
   export function useScoreUpdates(tournamentId: number | undefined) {
     const queryClient = useQueryClient()
     
     useEffect(() => {
       if (!tournamentId) return
       
       const eventSource = new EventSource(
         `${API_URL}/api/scores/stream/${tournamentId}`
       )
       
       eventSource.onmessage = (event) => {
         const data = JSON.parse(event.data)
         if (data.type === 'scores_updated') {
           // Invalidate and refetch leaderboard
           queryClient.invalidateQueries(['leaderboard', tournamentId])
         }
       }
       
       eventSource.onerror = () => {
         // Handle reconnection
         eventSource.close()
         setTimeout(() => {
           // Reconnect after delay
         }, 5000)
       }
       
       return () => eventSource.close()
     }, [tournamentId])
   }
   ```

2. **Replace Polling**
   - Remove `refetchInterval` from `useLeaderboard`
   - Use SSE hook instead
   - Keep polling as fallback if SSE fails

3. **Visual Indicators**
   - "Live" indicator when connected
   - Connection status (connected/disconnected/reconnecting)
   - Smooth transitions when updates arrive

### Database Considerations

**Option 1: Poll Database** (Simpler)
- SSE endpoint polls database every 2-5 seconds
- Checks for new `ScoreSnapshot` records
- Pros: Simple, no additional infrastructure
- Cons: Database queries every few seconds

**Option 2: Redis Pub/Sub** (Better for Scale)
- When scores calculated, publish event to Redis
- SSE endpoints subscribe to Redis channel
- Pros: Efficient, scales to multiple servers
- Cons: Requires Redis infrastructure

**Recommendation**: Start with Option 1, upgrade to Option 2 if needed.

### Deployment Considerations

1. **Railway/Render**
   - SSE connections count as active connections
   - May need to adjust connection limits
   - Consider connection timeout settings

2. **Load Balancing**
   - If using multiple servers, need Redis pub/sub
   - Or use sticky sessions (same server for same client)

3. **Monitoring**
   - Track active SSE connections
   - Monitor connection drop rate
   - Alert on high reconnection rates

### Fallback Strategy

**Hybrid Approach**:
1. Try SSE connection first
2. If SSE fails, fall back to polling
3. Show connection status to user
4. Automatically retry SSE connection

### Testing Strategy

1. **Unit Tests**
   - Test SSE endpoint generation
   - Test event formatting
   - Test connection handling

2. **Integration Tests**
   - Test full flow: calculate scores → SSE broadcast → client receives
   - Test reconnection logic
   - Test multiple concurrent connections

3. **Load Tests**
   - Test with 50+ concurrent connections
   - Verify server handles connections efficiently
   - Check memory usage over time

### Migration Path

**Phase 1: Add SSE (Keep Polling)**
- Add SSE endpoint
- Add SSE hook to frontend
- Keep polling as fallback
- A/B test: some users get SSE, others polling

**Phase 2: Make SSE Default**
- Make SSE the primary method
- Keep polling as fallback only
- Monitor connection success rate

**Phase 3: Remove Polling**
- Once SSE is stable, remove polling
- Monitor for any issues

### Alternative: WebSocket Implementation

If bidirectional communication is needed later:

**WebSocket Features**:
- Full duplex (client ↔ server)
- Lower overhead than SSE
- More complex to implement
- Better for chat, notifications, etc.

**When to Use WebSockets**:
- Need client-to-server messages (e.g., user actions)
- Need lower latency (< 100ms)
- Need binary data transfer
- Have infrastructure to support it

**For This Project**: SSE is sufficient - we only need server → client updates.

### Benefits
- ⚡ **Instant Updates**: < 1 second delay vs 0-30 second delay
- 📉 **Reduced Server Load**: 99% reduction in unnecessary API calls
- 🔋 **Battery Efficient**: One persistent connection vs constant polling
- 👥 **Synchronized Updates**: All users see changes simultaneously
- 🎯 **Better UX**: More engaging, "live" tournament feel
- 💰 **Cost Savings**: Fewer API calls = lower infrastructure costs

### Technical Considerations
- **Connection Limits**: Monitor active SSE connections
- **Reconnection Logic**: Handle network interruptions gracefully
- **Heartbeat**: Send periodic messages to keep connection alive
- **Error Handling**: Graceful degradation to polling if SSE fails
- **Scaling**: Use Redis pub/sub for multi-server deployments

### Estimated Implementation Time
- **Backend SSE Endpoint**: 4-6 hours
- **Frontend SSE Hook**: 2-3 hours
- **Testing & Polish**: 2-3 hours
- **Total**: ~1-2 days

---

## Phase 13: Email Notifications

### Features
- **Automated Emails**
  - Daily score summaries
  - Round completion notifications
  - Leaderboard position changes
  - Tournament start/end notifications

- **Email Templates**
  - HTML email templates
  - Personalized content
  - Mobile-friendly design

- **Notification Preferences**
  - User-configurable notification settings
  - Frequency controls (daily, per-round, etc.)

### Benefits
- Keep participants engaged
- Reduce need to check website constantly
- Better tournament experience

---

## Phase 14: Tournament History & Analytics

### Features
- **Historical Data**
  - View past tournaments
  - Compare tournaments
  - Historical leaderboards
  - Archive completed tournaments

- **Analytics Dashboard**
  - Entry statistics
  - Player performance tracking
  - Most popular player picks
  - Win/loss records
  - Average scores per tournament

- **Statistics**
  - Best performing entries
  - Most consistent participants
  - Tournament trends
  - Player selection patterns

### Benefits
- Long-term engagement
- Data-driven insights
- Competitive tracking
- Historical context

---

## Phase 15: Enhanced Admin Features

### Features
- **Advanced Import Options**
  - Excel file support (beyond CSV)
  - Bulk entry editing
  - Entry validation before import
  - Import history/audit log

- **Tournament Management**
  - Create/edit tournaments manually
  - Tournament templates
  - Multiple active tournaments
  - Tournament settings (scoring rules, etc.)

- **User Management**
  - Participant management
  - Entry assignment
  - Bulk operations
  - User activity logs

- **Reporting**
  - Export leaderboards to PDF/Excel
  - Custom reports
  - Email reports
  - Scheduled reports

### Benefits
- More efficient administration
- Better data management
- Professional reporting
- Easier tournament setup

---

## Phase 16: Mobile App (Optional)

### Features
- **Native Mobile App**
  - React Native or Flutter app
  - Push notifications
  - Offline viewing (cached data)
  - Better mobile UX

- **Progressive Web App (PWA)**
  - Installable on mobile
  - Offline support
  - Push notifications
  - App-like experience

### Benefits
- Better mobile experience
- Native app feel
- Push notifications
- Offline access

---

## Phase 17: Performance & Scalability

### Features
- **Caching**
  - Redis caching for API responses
  - Cache leaderboard data
  - Reduce API calls
  - Faster page loads

- **Database Optimization**
  - Query optimization
  - Index optimization
  - Connection pooling improvements
  - Read replicas for scaling

- **CDN Integration**
  - Static asset CDN
  - Faster global access
  - Reduced server load

- **Background Job Queue**
  - Replace in-memory jobs with Celery/RQ
  - Better job persistence
  - Job retry logic
  - Job monitoring

### Benefits
- Faster performance
- Better scalability
- Reduced costs
- More reliable

---

## Phase 18: Advanced Features

### Features
- **Entry Draft System**
  - Draft-style player selection
  - Prevent duplicate picks
  - Time-limited selections
  - Draft order management

- **Live Scoring Widget**
  - Embeddable leaderboard widget
  - Real-time updates
  - Customizable styling
  - Share on other websites

- **Social Features**
  - Share entry on social media
  - Comment system
  - Participant profiles
  - Achievement badges

- **Predictions & Betting**
  - Pre-tournament predictions
  - Confidence levels
  - Prediction leaderboard
  - Integration with betting (if legal)

### Benefits
- More engagement
- Social sharing
- Competitive elements
- Additional revenue opportunities

---

## Phase 19: Testing & Quality

### Features
- **Comprehensive Testing**
  - E2E tests with Playwright/Cypress
  - Load testing
  - Security testing
  - Accessibility testing

- **Monitoring & Observability**
  - Application performance monitoring (APM)
  - Error tracking (Sentry)
  - Uptime monitoring
  - Performance metrics

- **CI/CD Improvements**
  - Automated testing in CI
  - Staging environment
  - Automated deployments
  - Rollback capabilities

### Benefits
- Higher quality
- Fewer bugs
- Better reliability
- Faster development

---

## Phase 20: Documentation & Onboarding

### Features
- **User Documentation**
  - User guide
  - FAQ section
  - Video tutorials
  - Interactive tutorials

- **Admin Documentation**
  - Admin guide
  - API documentation
  - Troubleshooting guides
  - Best practices

- **Developer Documentation**
  - Architecture documentation
  - Code comments
  - Development setup guide
  - Contribution guidelines

### Benefits
- Easier onboarding
- Reduced support burden
- Better maintainability
- Knowledge transfer

---

## Phase 21: Internationalization (i18n)

### Features
- **Multi-Language Support**
  - English, Spanish, etc.
  - Language switcher
  - Translated content
  - Localized dates/numbers

### Benefits
- Broader audience
- International tournaments
- Better accessibility

---

## Phase 22: Accessibility (a11y)

### Features
- **WCAG Compliance**
  - Screen reader support
  - Keyboard navigation
  - Color contrast improvements
  - ARIA labels

- **Accessibility Testing**
  - Automated a11y testing
  - Manual testing
  - User testing with assistive technologies

### Benefits
- Legal compliance
- Broader user base
- Better UX for all users

---

## Quick Wins (Low Effort, High Impact)

### Immediate Improvements
1. **Add loading states** - Better UX during data fetching
2. **Error boundaries** - Graceful error handling
3. **Toast notifications** - Better user feedback
4. **Keyboard shortcuts** - Power user features
5. **Dark mode** - User preference
6. **Export to CSV** - Quick data export
7. **Print-friendly pages** - Better printing
8. **Share buttons** - Social sharing
9. **Search functionality** - Find entries quickly
10. **Filters** - Filter leaderboard by criteria

---

## Priority Recommendations

### High Priority (Next 3-6 months)
1. **User Authentication** - Security and personalization
2. **Email Notifications** - Engagement and retention
3. **Tournament History** - Long-term value
4. **Performance Optimization** - Better UX

### Medium Priority (6-12 months)
1. **Real-Time Updates** - Better UX
2. **Enhanced Admin Features** - Efficiency
3. **Analytics Dashboard** - Insights
4. **Mobile App/PWA** - Mobile experience

### Low Priority (12+ months)
1. **Advanced Features** - Nice-to-have
2. **Internationalization** - If needed
3. **Accessibility** - Compliance
4. **Social Features** - Engagement

---

## Notes

- Prioritize based on user feedback
- Focus on features that add real value
- Consider maintenance burden
- Balance new features with stability
- Regular user surveys to guide priorities

---

## Questions to Consider

1. **What do users request most?**
2. **What causes the most support issues?**
3. **What would increase engagement?**
4. **What would save admin time?**
5. **What would differentiate this from competitors?**

---

*Last Updated: January 2026*
