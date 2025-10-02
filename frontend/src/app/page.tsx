'use client';

import { useState } from 'react';

interface TradeEvaluation {
  grade: string;
  fairness_score: number;
  winner: string;
  summary: string;
  team_a_analysis: string;
  team_b_analysis: string;
  risks: string[];
  recommendation: string;
}

export default function Home() {
  const [teamA, setTeamA] = useState('');
  const [teamAGets, setTeamAGets] = useState('');
  const [teamB, setTeamB] = useState('');
  const [teamBGets, setTeamBGets] = useState('');
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TradeEvaluation | null>(null);
  const [error, setError] = useState('');

  const evaluateTrade = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          team_a: teamA,
          team_a_gets: teamAGets.split(',').map(s => s.trim()).filter(Boolean),
          team_b: teamB,
          team_b_gets: teamBGets.split(',').map(s => s.trim()).filter(Boolean),
          context: context || undefined
        })
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to evaluate trade');
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade: string) => {
    const letter = grade.charAt(0);
    if (letter === 'A') return 'text-green-600';
    if (letter === 'B') return 'text-blue-600';
    if (letter === 'C') return 'text-yellow-600';
    if (letter === 'D') return 'text-orange-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">⚾ MLB Trade Analyzer</h1>
          <p className="text-gray-600">AI-powered trade evaluation</p>
        </header>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Propose a Trade</h2>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Team A</label>
                <input
                  type="text"
                  placeholder="Yankees"
                  value={teamA}
                  onChange={(e) => setTeamA(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Team A Gets</label>
                <input
                  type="text"
                  placeholder="Juan Soto, Prospect A"
                  value={teamAGets}
                  onChange={(e) => setTeamAGets(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Team B</label>
                <input
                  type="text"
                  placeholder="Padres"
                  value={teamB}
                  onChange={(e) => setTeamB(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Team B Gets</label>
                <input
                  type="text"
                  placeholder="Clarke Schmidt, Top Prospect"
                  value={teamBGets}
                  onChange={(e) => setTeamBGets(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Context (Optional)</label>
              <textarea
                placeholder="Yankees need outfield help, Padres rebuilding..."
                value={context}
                onChange={(e) => setContext(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <button
              onClick={evaluateTrade}
              disabled={loading || !teamA || !teamAGets || !teamB || !teamBGets}
              className="w-full bg-blue-600 text-white py-3 rounded-md font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Analyzing...' : 'Evaluate Trade'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {result && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Trade Evaluation</h2>
              <div className="text-right">
                <div className={`text-3xl font-bold ${getGradeColor(result.grade)}`}>
                  {result.grade}
                </div>
                <div className="text-sm text-gray-600">
                  Fairness: {result.fairness_score}/100
                </div>
              </div>
            </div>

            <div className="mb-4 p-4 bg-blue-50 rounded-md">
              <p className="text-gray-800">{result.summary}</p>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="p-4 bg-gray-50 rounded-md">
                <h3 className="font-semibold text-gray-900 mb-2">{teamA}</h3>
                <p className="text-sm text-gray-700">{result.team_a_analysis}</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-md">
                <h3 className="font-semibold text-gray-900 mb-2">{teamB}</h3>
                <p className="text-sm text-gray-700">{result.team_b_analysis}</p>
              </div>
            </div>

            <div className="mb-4">
              <h3 className="font-semibold text-gray-900 mb-2">⚠️ Risks</h3>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {result.risks.map((risk, i) => (
                  <li key={i}>{risk}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 bg-green-50 rounded-md">
              <h3 className="font-semibold text-gray-900 mb-2">💡 Recommendation</h3>
              <p className="text-sm text-gray-700">{result.recommendation}</p>
            </div>

            <div className="mt-4 text-center text-sm text-gray-500">
              Winner: <span className="font-semibold">{result.winner}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
