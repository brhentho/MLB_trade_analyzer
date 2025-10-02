#!/usr/bin/env python3
"""
Direct test of MVP trade evaluation without needing localhost
Tests the core AI functionality directly
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import OpenAI
from openai import AsyncOpenAI

# MLB Expert Prompt (same as in mvp_main.py)
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

async def evaluate_trade_direct():
    """Evaluate a trade directly without starting the server"""

    print("🧪 Direct MVP Test (No Localhost Required)")
    print("=" * 50)
    print()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return

    print(f"✅ OpenAI API key found: {api_key[:20]}...")
    print()

    # Create OpenAI client
    client = AsyncOpenAI(api_key=api_key)

    # Test trade
    trade_proposal = {
        "team_a": "Yankees",
        "team_a_gets": ["Juan Soto"],
        "team_b": "Padres",
        "team_b_gets": ["Clarke Schmidt", "Top Prospect"],
        "context": "Yankees need power bat, Padres rebuilding"
    }

    print("📋 Trade Proposal:")
    print(f"   {trade_proposal['team_a']} receives: {', '.join(trade_proposal['team_a_gets'])}")
    print(f"   {trade_proposal['team_b']} receives: {', '.join(trade_proposal['team_b_gets'])}")
    print(f"   Context: {trade_proposal['context']}")
    print()

    # Build trade description
    trade_text = f"""
TRADE PROPOSAL:

{trade_proposal['team_a']} receives: {', '.join(trade_proposal['team_a_gets'])}
{trade_proposal['team_b']} receives: {', '.join(trade_proposal['team_b_gets'])}

Context: {trade_proposal['context']}
"""

    print("🤖 Calling OpenAI GPT-4o...")
    print()

    try:
        # Call OpenAI (same as mvp_main.py)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": MLB_EXPERT_PROMPT},
                {"role": "user", "content": trade_text}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)

        # Display results
        print("✅ AI Trade Evaluation:")
        print("=" * 50)
        print()
        print(f"Grade: {result['grade']}")
        print(f"Fairness Score: {result['fairness_score']}/100")
        print(f"Winner: {result['winner']}")
        print()
        print(f"Summary:")
        print(f"  {result['summary']}")
        print()
        print(f"{trade_proposal['team_a']} Analysis:")
        print(f"  {result['team_a_analysis']}")
        print()
        print(f"{trade_proposal['team_b']} Analysis:")
        print(f"  {result['team_b_analysis']}")
        print()
        print("Risks:")
        for risk in result['risks']:
            print(f"  ⚠️  {risk}")
        print()
        print("Recommendation:")
        print(f"  {result['recommendation']}")
        print()
        print("=" * 50)
        print("✅ Test Complete!")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(evaluate_trade_direct())
