"""
MLB Trade Analyzer - MVP
Simple OpenAI-powered trade evaluation
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create FastAPI app
app = FastAPI(
    title="MLB Trade Analyzer",
    description="AI-powered MLB trade evaluation",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MLB Expert System Prompt
MLB_EXPERT_PROMPT = """You are an expert MLB General Manager and trade analyst.

When evaluating trades, consider:
1. **Fair Value**: Are both teams getting equal value based on player performance, age, and potential?
2. **Team Fit**: Does each player fill a need for their new team?
3. **Contracts**: Salary implications and years of team control
4. **Risk Factors**: Injury history, performance trends, age decline
5. **Baseball Context**: Competitive windows, farm system depth, market size

Provide honest, analytical assessments. Be specific about WHY a trade works or doesn't.

Output Format (JSON):
{
  "grade": "A-F letter grade",
  "fairness_score": 0-100,
  "winner": "team_a, team_b, or even",
  "summary": "2-3 sentence overview",
  "team_a_analysis": "What team A gets/gives up",
  "team_b_analysis": "What team B gets/gives up",
  "risks": ["risk 1", "risk 2"],
  "recommendation": "Accept/Reject/Negotiate with reasoning"
}"""

# Request/Response Models
class TradeProposal(BaseModel):
    team_a: str = Field(..., description="First team (e.g., 'Yankees')")
    team_a_gets: List[str] = Field(..., description="Players/prospects team A receives")
    team_b: str = Field(..., description="Second team (e.g., 'Padres')")
    team_b_gets: List[str] = Field(..., description="Players/prospects team B receives")
    context: Optional[str] = Field(None, description="Additional context (needs, budget, etc.)")

class TradeEvaluation(BaseModel):
    grade: str
    fairness_score: int
    winner: str
    summary: str
    team_a_analysis: str
    team_b_analysis: str
    risks: List[str]
    recommendation: str

# Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "MLB Trade Analyzer MVP",
        "status": "operational",
        "version": "1.0.0",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.post("/api/evaluate", response_model=TradeEvaluation)
async def evaluate_trade(proposal: TradeProposal):
    """Evaluate a trade proposal using AI"""

    # Check OpenAI key
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured"
        )

    # Build trade description
    trade_text = f"""
TRADE PROPOSAL:

{proposal.team_a} receives: {', '.join(proposal.team_a_gets)}
{proposal.team_b} receives: {', '.join(proposal.team_b_gets)}
"""

    if proposal.context:
        trade_text += f"\nContext: {proposal.context}"

    try:
        # Call OpenAI
        logger.info(f"Evaluating trade: {proposal.team_a} ↔ {proposal.team_b}")

        response = await client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o for speed and quality
            messages=[
                {"role": "system", "content": MLB_EXPERT_PROMPT},
                {"role": "user", "content": trade_text}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        # Parse response
        import json
        result = json.loads(response.choices[0].message.content)

        logger.info(f"Trade evaluated: Grade {result.get('grade')}")

        return TradeEvaluation(**result)

    except Exception as e:
        logger.error(f"Error evaluating trade: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.get("/api/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "openai_available": bool(os.getenv("OPENAI_API_KEY")),
        "model": "gpt-4o"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
