'use client';

import { useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Users, 
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Star
} from 'lucide-react';
import { type TradeAnalysis, type TradeRecommendation } from '@/lib/api';

interface ResultsDisplayProps {
  analysis: TradeAnalysis;
}

export default function ResultsDisplay({ analysis }: ResultsDisplayProps) {
  const [activeTab, setActiveTab] = useState('overview');

  // Extract actual results from analysis or use fallback
  const hasResults = analysis.recommendations && analysis.recommendations.length > 0;
  
  // Use actual results or mock data for demo
  const recommendations = hasResults ? analysis.recommendations : [
    {
      priority: 1,
      player_target: "Juan Soto",
      current_team: "San Diego Padres",
      position: "OF",
      trade_package: ["Top prospect package", "Salary relief"],
      organizational_consensus: "Strong support from all departments",
      key_benefits: [
        "Elite offensive production",
        "Young superstar with upside",
        "Playoff experience"
      ],
      risks: [
        "Very expensive trade cost",
        "Large contract commitment",
        "Limited defensive value"
      ],
      financial_impact: {
        salary_added: 35000000,
        luxury_tax_impact: 40000000,
        total_cost: 105000000
      },
      implementation_timeline: "2-4 weeks",
      confidence_level: 0.85
    }
  ];

  // Extract or create summary information
  const analysisSummary = analysis.front_office_analysis?.summary || 
    `Based on your request for "${analysis.original_request}", our AI system identified ${recommendations.length} viable trade target(s). The analysis considers your team's competitive window, budget constraints, and organizational needs.`;

  // Calculate financial impact from recommendations
  const totalSalaryAdded = recommendations.reduce((total, rec) => 
    total + (rec.financial_impact?.salary_added || 0), 0);
  const totalLuxuryTaxImpact = recommendations.reduce((total, rec) => 
    total + (rec.financial_impact?.luxury_tax_impact || 0), 0);

  const financialData = {
    estimated_cost: totalSalaryAdded || 25000000,
    luxury_tax_impact: totalLuxuryTaxImpact || 10000000,
    years_committed: 3, // Default
    risk_level: totalSalaryAdded > 50000000 ? "high" : totalSalaryAdded > 25000000 ? "medium" : "low"
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'recommendations', name: 'Trade Targets', icon: Users },
    { id: 'financial', name: 'Financial Impact', icon: DollarSign },
    { id: 'details', name: 'AI Analysis', icon: Star }
  ];

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-600 bg-gray-50';
    if (confidence >= 0.8) return 'text-green-600 bg-green-50';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getConfidenceLabel = (confidence?: number) => {
    if (!confidence) return 'unknown';
    if (confidence >= 0.8) return 'high confidence';
    if (confidence >= 0.6) return 'medium confidence';
    return 'low confidence';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Trade Analysis Results
            </h3>
            <p className="text-sm text-gray-600">
              AI-powered recommendations for {analysis.team}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            <span className="text-sm font-medium text-green-600">Analysis Complete</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="px-6">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const TabIcon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <TabIcon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Analysis Summary</h4>
              <p className="text-gray-700 leading-relaxed">
                {analysisSummary}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  <span className="font-medium text-blue-900">Trade Targets</span>
                </div>
                <div className="text-2xl font-bold text-blue-600 mt-1">
                  {recommendations.length}
                </div>
                <p className="text-sm text-blue-700">Viable options identified</p>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-900">Best Match</span>
                </div>
                <div className="text-lg font-bold text-green-600 mt-1">
                  {recommendations[0]?.player_target || 'Analyzing...'}
                </div>
                <p className="text-sm text-green-700">Top recommendation</p>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <DollarSign className="h-5 w-5 text-yellow-600" />
                  <span className="font-medium text-yellow-900">Est. Cost</span>
                </div>
                <div className="text-lg font-bold text-yellow-600 mt-1">
                  ${(financialData.estimated_cost / 1000000).toFixed(1)}M
                </div>
                <p className="text-sm text-yellow-700">Per year average</p>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {recommendations.map((rec, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center space-x-3">
                      <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2 py-1 rounded">
                        #{rec.priority}
                      </span>
                      <h4 className="text-lg font-semibold text-gray-900">
                        {rec.player_target}
                      </h4>
                      <span className="text-gray-500">•</span>
                      <span className="text-gray-600">{rec.current_team}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {rec.position} • Timeline: {rec.implementation_timeline}
                    </p>
                  </div>
                  <span className={`px-3 py-1 text-sm font-medium rounded-full ${getConfidenceColor(rec.confidence_level)}`}>
                    {getConfidenceLabel(rec.confidence_level)}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Trade Package */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">Trade Package</h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {rec.trade_package.map((item, i) => (
                        <li key={i} className="flex items-start space-x-1">
                          <span className="text-blue-500 mt-0.5">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Key Benefits */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                      <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                      Benefits
                    </h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {rec.key_benefits.map((benefit, i) => (
                        <li key={i} className="flex items-start space-x-1">
                          <span className="text-green-500 mt-0.5">•</span>
                          <span>{benefit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Risks */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2 flex items-center">
                      <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                      Risks
                    </h5>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {rec.risks.map((risk, i) => (
                        <li key={i} className="flex items-start space-x-1">
                          <span className="text-red-500 mt-0.5">•</span>
                          <span>{risk}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Financial Impact */}
                {rec.financial_impact && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <h5 className="font-medium text-gray-900 mb-2">Financial Impact</h5>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      {rec.financial_impact.salary_added && (
                        <div>
                          <span className="text-gray-600">Salary Added:</span>
                          <div className="font-medium">${(rec.financial_impact.salary_added / 1000000).toFixed(1)}M</div>
                        </div>
                      )}
                      {rec.financial_impact.luxury_tax_impact && (
                        <div>
                          <span className="text-gray-600">Tax Impact:</span>
                          <div className="font-medium">${(rec.financial_impact.luxury_tax_impact / 1000000).toFixed(1)}M</div>
                        </div>
                      )}
                      {rec.financial_impact.total_cost && (
                        <div>
                          <span className="text-gray-600">Total Cost:</span>
                          <div className="font-medium">${(rec.financial_impact.total_cost / 1000000).toFixed(1)}M</div>
                        </div>
                      )}
                      {rec.financial_impact.playoff_revenue_upside && (
                        <div>
                          <span className="text-gray-600">Upside:</span>
                          <div className="font-medium text-green-600">${(rec.financial_impact.playoff_revenue_upside / 1000000).toFixed(1)}M</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Organizational Consensus */}
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <h5 className="font-medium text-gray-900 mb-1">Organizational Consensus</h5>
                  <p className="text-sm text-gray-600">{rec.organizational_consensus}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Financial Tab */}
        {activeTab === 'financial' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3">Cost Breakdown</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Annual Salary Cost:</span>
                    <span className="font-medium">${(financialData.estimated_cost / 1000000).toFixed(1)}M</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Luxury Tax Impact:</span>
                    <span className="font-medium">${(financialData.luxury_tax_impact / 1000000).toFixed(1)}M</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Contract Length:</span>
                    <span className="font-medium">{financialData.years_committed} years</span>
                  </div>
                  <div className="flex justify-between border-t pt-3">
                    <span className="text-gray-600">Risk Level:</span>
                    <span className={`font-medium capitalize ${getRiskColor(financialData.risk_level)}`}>
                      {financialData.risk_level}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-3">
                  <AlertTriangle className="h-5 w-5 text-yellow-600" />
                  <h4 className="font-medium text-yellow-900">Financial Considerations</h4>
                </div>
                <ul className="text-sm text-yellow-800 space-y-2">
                  <li>• Salary impact varies by specific player acquired</li>
                  <li>• Consider including salary relief in trade packages</li>
                  <li>• Luxury tax calculations depend on final roster composition</li>
                  <li>• Factor in potential performance bonuses and incentives</li>
                  <li>• Multi-year commitments affect future payroll flexibility</li>
                </ul>
              </div>
            </div>

            {/* Individual Player Financial Breakdown */}
            {recommendations.length > 0 && recommendations.some(r => r.financial_impact) && (
              <div>
                <h4 className="font-medium text-gray-900 mb-4">Per-Player Financial Impact</h4>
                <div className="space-y-3">
                  {recommendations.filter(r => r.financial_impact).map((rec, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h5 className="font-medium text-gray-900">{rec.player_target}</h5>
                        <span className="text-sm text-gray-500">Priority #{rec.priority}</span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        {rec.financial_impact?.salary_added && (
                          <div>
                            <span className="text-gray-600">Annual Salary:</span>
                            <div className="font-medium">${(rec.financial_impact.salary_added / 1000000).toFixed(1)}M</div>
                          </div>
                        )}
                        {rec.financial_impact?.luxury_tax_impact && (
                          <div>
                            <span className="text-gray-600">Tax Impact:</span>
                            <div className="font-medium">${(rec.financial_impact.luxury_tax_impact / 1000000).toFixed(1)}M</div>
                          </div>
                        )}
                        {rec.financial_impact?.total_cost && (
                          <div>
                            <span className="text-gray-600">Total Cost:</span>
                            <div className="font-medium">${(rec.financial_impact.total_cost / 1000000).toFixed(1)}M</div>
                          </div>
                        )}
                        {rec.financial_impact?.playoff_revenue_upside && (
                          <div>
                            <span className="text-gray-600">Revenue Upside:</span>
                            <div className="font-medium text-green-600">+${(rec.financial_impact.playoff_revenue_upside / 1000000).toFixed(1)}M</div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Details Tab */}
        {activeTab === 'details' && (
          <div className="space-y-6">
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Analysis Metadata</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Analysis Info</h5>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Analysis ID:</span>
                      <span className="font-mono text-xs">{analysis.analysis_id}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <span className="capitalize font-medium">{analysis.status}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Requested:</span>
                      <span>{new Date(analysis.analysis_timestamp).toLocaleString()}</span>
                    </div>
                    {analysis.completed_at && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Completed:</span>
                        <span>{new Date(analysis.completed_at).toLocaleString()}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Departments Consulted</h5>
                  <div className="space-y-1">
                    {analysis.departments_consulted.length > 0 ? (
                      analysis.departments_consulted.map((dept, index) => (
                        <div key={index} className="flex items-center space-x-2 text-sm">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          <span>{dept}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">No departments consulted yet</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Original Request */}
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Original Request</h4>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-gray-700">
                  <strong>Team:</strong> {analysis.team}
                </p>
                <p className="text-gray-700 mt-2">
                  <strong>Request:</strong> &ldquo;{analysis.original_request}&rdquo;
                </p>
              </div>
            </div>

            {/* Parsed Request (if available) */}
            {analysis.parsed_request && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Request Analysis</h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                    {JSON.stringify(analysis.parsed_request, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Front Office Analysis (if available) */}
            {analysis.front_office_analysis && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Front Office Analysis</h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                    {JSON.stringify(analysis.front_office_analysis, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Cost Information (if available) */}
            {analysis.cost_info && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">AI Cost Information</h4>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                    {JSON.stringify(analysis.cost_info, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Error Information (if any) */}
            {analysis.error_message && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Error Details</h4>
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <p className="text-red-700">{analysis.error_message}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}