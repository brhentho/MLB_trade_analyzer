# Baseball Trade AI Project Context

## Project Overview
Baseball Trade AI is a web application that simulates realistic MLB trades using AI-powered multi-agent systems. Users can find trades through natural language queries ("find me a starting pitcher with ERA under 4.0") or build them manually with drag-and-drop interfaces.

## Core Technologies
- **Backend**: Python 3.11+, FastAPI, CrewAI, LangChain, Supabase
- **Frontend**: Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Database**: Supabase (PostgreSQL with Row Level Security)
- **AI**: OpenAI GPT-4/GPT-3.5, CrewAI for multi-agent orchestration
- **Deployment**: Vercel (frontend), Railway (backend)

## Project Structure
```
baseball-trade-ai/
├── backend/
│   ├── agents/           # CrewAI agent definitions
│   ├── api/              # FastAPI endpoints
│   ├── crews/            # Multi-agent orchestration
│   ├── tools/            # Agent tools (stats, salary, roster)
│   ├── database/         # Models and queries
│   └── tests/
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   ├── lib/              # API clients and utilities
│   └── tests/
└── supabase/
    └── migrations/       # Database migrations
```

## Key Features
1. **Mad Libs Trade Finder**: Natural language trade search using AI agents
2. **Manual Trade Builder**: Drag-and-drop interface with real-time evaluation
3. **AI Evaluation Engine**: Multi-agent system that evaluates trades like real GMs
4. **Team Dashboards**: Comprehensive team analysis and trade possibilities
5. **Community Features**: Share and discuss trades with other fans

## AI Agent Architecture
The system uses CrewAI with specialized agents:
- **TradeCoordinator**: Orchestrates the entire evaluation process
- **30 Team GM Agents**: One for each MLB team with team-specific knowledge
- **StatsAnalyst**: Analyzes player statistics and projections
- **SalaryCapExpert**: Evaluates financial implications and luxury tax
- **ProspectEvaluator**: Values prospects using industry-standard metrics
- **TradeNegotiator**: Structures deals that work for all parties

## Code Style Guidelines

### Python Backend
```python
# Always use type hints and async/await
async def evaluate_trade(
    trade_data: TradeProposal,
    user_id: str
) -> TradeEvaluation:
    """Evaluate trade using CrewAI agents."""
    crew = TradeEvaluatorCrew()
    result = await crew.kickoff_async(trade_data)
    return TradeEvaluation.from_crew_result(result)
```

### TypeScript Frontend
```typescript
// Use interfaces and proper error handling
interface TradeProposal {
  teamA: TeamTrade;
  teamB: TeamTrade;
  teamC?: TeamTrade;
}

export async function evaluateTrade(
  proposal: TradeProposal
): Promise<TradeEvaluation> {
  const validated = TradeProposalSchema.parse(proposal);
  const response = await api.post('/trades/evaluate', validated);
  return response.data;
}
```

## CrewAI Implementation Patterns
```python
# Agent factory pattern
class AgentFactory:
    @staticmethod
    def create_gm_agent(team: str) -> Agent:
        return Agent(
            role=f"{team} General Manager",
            goal=f"Improve {team} roster within constraints",
            backstory=get_team_backstory(team),
            tools=[roster_tool, stats_tool, salary_tool],
            max_iter=3,  # Prevent infinite loops
            memory=True
        )

# Tool creation with validation
@tool
def get_player_stats(player_name: str, season: int = 2024) -> dict:
    """Get player statistics for evaluation."""
    if not player_name or len(player_name) < 2:
        raise ValueError("Invalid player name")
    
    return {
        "player": player_name,
        "stats": fetch_stats(player_name, season),
        "source": "baseball-reference",
        "updated_at": datetime.now().isoformat()
    }
```

## API Endpoints
- `POST /api/trades/find` - Natural language trade search
- `POST /api/trades/evaluate` - Evaluate manual trade
- `GET /api/teams/{id}/roster` - Get team roster
- `GET /api/teams/{id}/needs` - AI-analyzed team needs
- `GET /api/players/search` - Search players

## Database Schema Highlights
- **teams**: All 30 MLB teams with payroll info
- **players**: Current rosters with contracts and stats cache
- **prospects**: Minor league players with rankings
- **trade_proposals**: User-created trades with AI evaluations
- **trade_reactions**: Community engagement data

## Environment Variables Required
```bash
# Backend
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
REDIS_URL=

# Frontend
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=
```

## Performance Considerations
- Cache player stats for 24 hours
- Use GPT-3.5 for simple queries, GPT-4 for complex evaluations
- Implement request queuing for multi-team trades
- Target < 30s for trade generation, < 10s for evaluation

## Security Requirements
- All API endpoints require authentication except public trade viewing
- Rate limiting: 10 trades per minute per user
- Sanitize all user inputs
- Use Supabase RLS for data access control
- Never expose service keys to frontend

## Testing Strategy
- Mock LLM responses in tests
- Unit test coverage > 80%
- Integration tests for agent communication
- E2E tests for critical user journeys

## Common Pitfalls to Avoid
1. Don't fetch all data - always paginate
2. Don't trust client data - validate server-side
3. Don't skip error handling - log and handle gracefully
4. Don't hardcode values - use environment variables
5. Don't ignore TypeScript types - they prevent bugs

## Cost Management
- Monitor OpenAI token usage closely
- Implement fallbacks from GPT-4 to GPT-3.5
- Cache aggressively (evaluations, stats, rosters)
- Set user quotas for free tier

## Baseball Domain Knowledge
- Trades must follow MLB rules (40-man roster, service time, etc.)
- Consider no-trade clauses and 10-and-5 rights
- Luxury tax calculations affect trade decisions
- Prospect values use 20-80 FV (Future Value) scale
- WAR (Wins Above Replacement) is key metric

## Current Development Status
- Starting fresh project
- Focus on MVP: Mad Libs finder + basic evaluation
- CrewAI chosen for multi-agent orchestration
- Supabase for database and auth
- Planning 2-month timeline to launch

## Remember
- User experience first - trades must feel realistic
- Baseball accuracy matters - use real rules and data
- AI should enhance, not replace baseball knowledge
- Performance is critical during trade deadline
- Community features drive retention