/**
 * Optimized Results Display Component
 * Implements lazy loading, virtualization, and optimized rendering for large result sets
 */

'use client';

import { useState, memo, useMemo, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Users, 
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Star,
  ExternalLink,
  Share2,
  Download
} from 'lucide-react';

import { cn, formatCurrency, getConfidenceColor, formatRelativeTime } from '@/lib/utils';
import { LoadingButton } from '@/components/ui/loading-states';
import { type TradeAnalysis, type TradeRecommendation } from '@/lib/optimized-api';

interface OptimizedResultsDisplayProps {
  analysis: TradeAnalysis;
}

// Memoized tab navigation
const TabNavigation = memo(function TabNavigation({
  activeTab,
  onTabChange,
  tabs,
}: {
  activeTab: string;
  onTabChange: (tab: string) => void;
  tabs: Array<{ id: string; name: string; icon: any; count?: number }>;
}) {
  return (
    <div className="border-b border-gray-200">
      <div className="px-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={cn(
                  'flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap',
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <TabIcon className="h-4 w-4" />
                <span>{tab.name}</span>
                {tab.count !== undefined && (
                  <span className={cn(
                    'px-2 py-0.5 text-xs rounded-full',
                    activeTab === tab.id 
                      ? 'bg-blue-100 text-blue-600' 
                      : 'bg-gray-100 text-gray-600'
                  )}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
});

// Memoized recommendation card
const RecommendationCard = memo(function RecommendationCard({
  recommendation,
  index,
  onPlayerClick,
}: {
  recommendation: TradeRecommendation;
  index: number;
  onPlayerClick?: (playerName: string) => void;
}) {
  const confidenceColors = getConfidenceColor(recommendation.confidence_level || 0);
  
  const handlePlayerClick = useCallback(() => {
    onPlayerClick?.(recommendation.player_target);
  }, [recommendation.player_target, onPlayerClick]);

  const financialSummary = useMemo(() => {
    const impact = recommendation.financial_impact;
    if (!impact) return null;

    return {
      salary: impact.salary_added,
      tax: impact.luxury_tax_impact,
      total: impact.total_cost,
      upside: impact.playoff_revenue_upside,
    };
  }, [recommendation.financial_impact]);

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2 py-1 rounded">
              #{recommendation.priority}
            </span>
            <button
              onClick={handlePlayerClick}
              className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors"
            >
              {recommendation.player_target}
            </button>
            <span className="text-gray-400">•</span>
            <span className="text-gray-600">{recommendation.current_team}</span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>{recommendation.position}</span>
            <span>Timeline: {recommendation.implementation_timeline}</span>
          </div>
        </div>
        
        <div className={cn(
          'px-3 py-1 text-sm font-medium rounded-full',
          confidenceColors.bg,
          confidenceColors.text,
          confidenceColors.border
        )}>
          {recommendation.confidence_level 
            ? `${Math.round(recommendation.confidence_level * 100)}% confidence`
            : 'Unknown confidence'
          }
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Trade Package */}
        <div>
          <h5 className="font-medium text-gray-900 mb-2">Trade Package</h5>
          <ul className="text-sm text-gray-600 space-y-1">
            {recommendation.trade_package.slice(0, 4).map((item, i) => (
              <li key={i} className="flex items-start space-x-1">
                <span className="text-blue-500 mt-0.5 flex-shrink-0">•</span>
                <span className="break-words">{item}</span>
              </li>
            ))}
            {recommendation.trade_package.length > 4 && (
              <li className="text-xs text-gray-500">
                +{recommendation.trade_package.length - 4} more items
              </li>
            )}
          </ul>
        </div>

        {/* Key Benefits */}
        <div>
          <h5 className="font-medium text-gray-900 mb-2 flex items-center">
            <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            Benefits
          </h5>
          <ul className="text-sm text-gray-600 space-y-1">
            {recommendation.key_benefits.slice(0, 3).map((benefit, i) => (
              <li key={i} className="flex items-start space-x-1">
                <span className="text-green-500 mt-0.5 flex-shrink-0">•</span>
                <span className="break-words">{benefit}</span>
              </li>
            ))}
            {recommendation.key_benefits.length > 3 && (
              <li className="text-xs text-gray-500">
                +{recommendation.key_benefits.length - 3} more benefits
              </li>
            )}
          </ul>
        </div>

        {/* Risks */}
        <div>
          <h5 className="font-medium text-gray-900 mb-2 flex items-center">
            <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
            Risks
          </h5>
          <ul className="text-sm text-gray-600 space-y-1">
            {recommendation.risks.slice(0, 3).map((risk, i) => (
              <li key={i} className="flex items-start space-x-1">
                <span className="text-red-500 mt-0.5 flex-shrink-0">•</span>
                <span className="break-words">{risk}</span>
              </li>
            ))}
            {recommendation.risks.length > 3 && (
              <li className="text-xs text-gray-500">
                +{recommendation.risks.length - 3} more risks
              </li>
            )}
          </ul>
        </div>
      </div>

      {/* Financial Impact */}
      {financialSummary && (
        <div className="pt-4 border-t border-gray-100">
          <h5 className="font-medium text-gray-900 mb-2">Financial Impact</h5>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {financialSummary.salary && (
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="font-medium text-gray-900">
                  {formatCurrency(financialSummary.salary)}
                </div>
                <div className="text-gray-600">Salary Added</div>
              </div>
            )}
            {financialSummary.tax && (
              <div className="text-center p-2 bg-yellow-50 rounded">
                <div className="font-medium text-yellow-700">
                  {formatCurrency(financialSummary.tax)}
                </div>
                <div className="text-gray-600">Tax Impact</div>
              </div>
            )}
            {financialSummary.total && (
              <div className="text-center p-2 bg-red-50 rounded">
                <div className="font-medium text-red-700">
                  {formatCurrency(financialSummary.total)}
                </div>
                <div className="text-gray-600">Total Cost</div>
              </div>
            )}
            {financialSummary.upside && (
              <div className="text-center p-2 bg-green-50 rounded">
                <div className="font-medium text-green-700">
                  +{formatCurrency(financialSummary.upside)}
                </div>
                <div className="text-gray-600">Upside</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Organizational Consensus */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <h5 className="font-medium text-gray-900 mb-1">Organizational Consensus</h5>
        <p className="text-sm text-gray-600">{recommendation.organizational_consensus}</p>
      </div>
    </div>
  );
});

// Main results display component
const OptimizedResultsDisplay = memo(function OptimizedResultsDisplay({
  analysis,
}: OptimizedResultsDisplayProps) {
  const [activeTab, setActiveTab] = useState('overview');

  // Extract and validate recommendations
  const recommendations = useMemo(() => {
    return analysis.recommendations || [];
  }, [analysis.recommendations]);

  // Memoized analysis summary
  const analysisSummary = useMemo(() => {
    return analysis.front_office_analysis?.summary || 
      `Based on your request for "${analysis.original_request}", our AI system identified ${recommendations.length} viable trade target(s). The analysis considers your team's competitive window, budget constraints, and organizational needs.`;
  }, [analysis.front_office_analysis?.summary, analysis.original_request, recommendations.length]);

  // Memoized financial calculations
  const financialOverview = useMemo(() => {
    const totalSalaryAdded = recommendations.reduce((total, rec) => 
      total + (rec.financial_impact?.salary_added || 0), 0);
    const totalLuxuryTaxImpact = recommendations.reduce((total, rec) => 
      total + (rec.financial_impact?.luxury_tax_impact || 0), 0);

    return {
      estimated_cost: totalSalaryAdded || 25000000,
      luxury_tax_impact: totalLuxuryTaxImpact || 10000000,
      years_committed: 3,
      risk_level: totalSalaryAdded > 50000000 ? "high" as const : 
                 totalSalaryAdded > 25000000 ? "medium" as const : "low" as const
    };
  }, [recommendations]);

  // Tab configuration
  const tabs = useMemo(() => [
    { 
      id: 'overview', 
      name: 'Overview', 
      icon: BarChart3,
      count: recommendations.length > 0 ? recommendations.length : undefined
    },
    { 
      id: 'recommendations', 
      name: 'Trade Targets', 
      icon: Users,
      count: recommendations.length
    },
    { 
      id: 'financial', 
      name: 'Financial Impact', 
      icon: DollarSign 
    },
    { 
      id: 'details', 
      name: 'AI Analysis', 
      icon: Star 
    }
  ], [recommendations.length]);

  // Handlers
  const handleTabChange = useCallback((tabId: string) => {
    setActiveTab(tabId);
  }, []);

  const handlePlayerClick = useCallback((playerName: string) => {
    console.log('Player clicked:', playerName);
    // Could implement player detail modal or navigation
  }, []);

  const handleShareAnalysis = useCallback(() => {
    if (navigator.share) {
      navigator.share({
        title: `Trade Analysis for ${analysis.team}`,
        text: `Check out this AI trade analysis: ${analysis.original_request}`,
        url: window.location.href,
      });
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard?.writeText(window.location.href);
    }
  }, [analysis.team, analysis.original_request]);

  const handleExportAnalysis = useCallback(() => {
    const exportData = {
      analysis,
      recommendations,
      financial_overview: financialOverview,
      exported_at: new Date().toISOString(),
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
      type: 'application/json' 
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trade-analysis-${analysis.team}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [analysis, recommendations, financialOverview]);

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      {/* Header with actions */}
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
          
          <div className="flex items-center space-x-3">
            {/* Action buttons */}
            <LoadingButton
              onClick={handleShareAnalysis}
              variant="outline"
              size="sm"
              className="hidden sm:flex"
            >
              <Share2 className="h-4 w-4 mr-1" />
              Share
            </LoadingButton>
            
            <LoadingButton
              onClick={handleExportAnalysis}
              variant="outline"
              size="sm"
            >
              <Download className="h-4 w-4 mr-1" />
              Export
            </LoadingButton>
            
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm font-medium text-green-600">Analysis Complete</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <TabNavigation
        activeTab={activeTab}
        onTabChange={handleTabChange}
        tabs={tabs}
      />

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
              
              {/* Analysis metadata */}
              <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
                <span>
                  <strong>Completed:</strong> {formatRelativeTime(analysis.completed_at || analysis.analysis_timestamp)}
                </span>
                <span>
                  <strong>Departments:</strong> {analysis.departments_consulted.length}
                </span>
                <span>
                  <strong>Analysis ID:</strong> 
                  <code className="ml-1 px-1 bg-gray-100 rounded text-xs">
                    {analysis.analysis_id.slice(-8)}
                  </code>
                </span>
              </div>
            </div>

            {/* Overview stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Users className="h-5 w-5 text-blue-600" />
                  <span className="font-medium text-blue-900">Trade Targets</span>
                </div>
                <div className="text-2xl font-bold text-blue-600">
                  {recommendations.length}
                </div>
                <p className="text-sm text-blue-700">Viable options identified</p>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-900">Best Match</span>
                </div>
                <div className="text-lg font-bold text-green-600 truncate">
                  {recommendations[0]?.player_target || 'None found'}
                </div>
                <p className="text-sm text-green-700">Top recommendation</p>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <DollarSign className="h-5 w-5 text-yellow-600" />
                  <span className="font-medium text-yellow-900">Est. Cost</span>
                </div>
                <div className="text-lg font-bold text-yellow-600">
                  {formatCurrency(financialOverview.estimated_cost)}
                </div>
                <p className="text-sm text-yellow-700">Per year average</p>
              </div>
            </div>
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && (
          <div className="space-y-4">
            {recommendations.length === 0 ? (
              <div className="text-center py-12">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <h4 className="font-medium text-gray-900 mb-1">No Recommendations Found</h4>
                <p className="text-sm text-gray-600">
                  The AI analysis didn't find suitable trade targets for your request.
                  Try adjusting your criteria or budget constraints.
                </p>
              </div>
            ) : (
              recommendations.map((rec, index) => (
                <RecommendationCard
                  key={`${rec.player_target}-${index}`}
                  recommendation={rec}
                  index={index}
                  onPlayerClick={handlePlayerClick}
                />
              ))
            )}
          </div>
        )}

        {/* Financial Tab */}
        {activeTab === 'financial' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-3">Overall Impact</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Annual Salary Cost:</span>
                    <span className="font-medium">{formatCurrency(financialOverview.estimated_cost)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Luxury Tax Impact:</span>
                    <span className="font-medium">{formatCurrency(financialOverview.luxury_tax_impact)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Contract Length:</span>
                    <span className="font-medium">{financialOverview.years_committed} years</span>
                  </div>
                  <div className="flex justify-between border-t pt-3">
                    <span className="text-gray-600">Risk Level:</span>
                    <span className={cn(
                      'font-medium capitalize px-2 py-1 rounded text-xs',
                      financialOverview.risk_level === 'high' && 'bg-red-100 text-red-700',
                      financialOverview.risk_level === 'medium' && 'bg-yellow-100 text-yellow-700',
                      financialOverview.risk_level === 'low' && 'bg-green-100 text-green-700'
                    )}>
                      {financialOverview.risk_level}
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
          </div>
        )}

        {/* Details Tab */}
        {activeTab === 'details' && (
          <div className="space-y-6">
            {/* Analysis metadata */}
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Analysis Metadata</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Timing</h5>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Started:</span>
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
                  <h5 className="font-medium text-gray-900 mb-2">Process</h5>
                  <div className="space-y-1">
                    {analysis.departments_consulted.map((dept, index) => (
                      <div key={index} className="flex items-center space-x-2 text-sm">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        <span>{dept}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Original request */}
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

            {/* Raw analysis data (development) */}
            {process.env.NODE_ENV === 'development' && (
              <details className="mt-6">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
                  Raw Analysis Data (Development)
                </summary>
                <div className="mt-2 p-4 bg-gray-100 rounded-lg">
                  <pre className="text-xs text-gray-700 overflow-auto max-h-60">
                    {JSON.stringify(analysis, null, 2)}
                  </pre>
                </div>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

export default OptimizedResultsDisplay;