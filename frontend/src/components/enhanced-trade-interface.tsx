/**
 * Enhanced Trade Interface Component
 * Comprehensive UX-optimized interface for Baseball Trade AI with accessibility
 */

'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import { 
  Search,
  BarChart3,
  Users,
  Building2,
  TrendingUp,
  Activity,
  Shield,
  Zap,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
} from 'lucide-react';

// Enhanced UI components
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge, PositionBadge } from '@/components/ui/badge';
import { Container, PageHeader, Grid, Stack } from '@/components/ui/layout';
import { Progress, AnalysisProgress, defaultAnalysisSteps } from '@/components/ui/progress';
import { TeamDropdown } from '@/components/ui/dropdown';
import { Input, Field, CurrencyInput } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import { Dialog, DialogContent, DialogHeader, DialogTitle, TradeDialog } from '@/components/ui/dialog';
import { 
  StatCard, 
  PerformanceMeter, 
  TradeComparison, 
  RosterVisualization,
  TradeImpact 
} from '@/components/ui/data-viz';
import {
  PlayerCardSkeleton,
  TeamCardSkeleton,
  TradeAnalysisSkeleton,
  PlayerSearchSkeleton
} from '@/components/ui/skeletons';

// API hooks and types (using existing structure)
import {
  useSystemHealth,
  useTeams,
  useTradeAnalysisMutation,
} from '@/hooks/use-api-queries';

interface EnhancedTradeInterfaceProps {
  className?: string;
}

export default function EnhancedTradeInterface({ className }: EnhancedTradeInterfaceProps) {
  // State management
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [tradeRequest, setTradeRequest] = useState('');
  const [urgency, setUrgency] = useState<'low' | 'medium' | 'high'>('medium');
  const [budgetLimit, setBudgetLimit] = useState<number | undefined>();
  const [currentAnalysis, setCurrentAnalysis] = useState<any>(null);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [activeTab, setActiveTab] = useState<'request' | 'manual' | 'history'>('request');

  // API hooks
  const systemHealthQuery = useSystemHealth();
  const teamsQuery = useTeams();
  const tradeAnalysisMutation = useTradeAnalysisMutation();

  // Derived state
  const selectedTeamData = useMemo(() => {
    if (!selectedTeam || !teamsQuery.data?.teams) return null;
    return teamsQuery.data.teams[selectedTeam] || null;
  }, [selectedTeam, teamsQuery.data?.teams]);

  const isSystemHealthy = systemHealthQuery.data?.status === 'operational';
  const isLoading = systemHealthQuery.isLoading || teamsQuery.isLoading;
  const hasError = systemHealthQuery.error || teamsQuery.error;

  // Example trade requests for better UX
  const exampleRequests = useMemo(() => [
    "I need a power bat with 30+ home runs",
    "Find me a starting pitcher with ERA under 3.50", 
    "Looking for a closer who can handle high leverage situations",
    "Need a shortstop with good defense and some pop",
    "Want a veteran leader for the clubhouse",
    "Looking for a cost-effective utility player",
    "Need bullpen depth for the playoff push",
    "Find me a left-handed reliever"
  ], []);

  // Department configuration for AI analysis
  const departments = useMemo(() => [
    {
      id: 'coordination',
      name: 'AI Coordinator',
      description: 'Orchestrates multi-agent analysis workflow',
      icon: Building2,
      color: 'bg-blue-500'
    },
    {
      id: 'scouting',
      name: 'Chief Scout',
      description: 'Player evaluation & scouting insights',
      icon: Search,
      color: 'bg-green-500'
    },
    {
      id: 'analytics', 
      name: 'Analytics Director',
      description: 'Statistical analysis & performance projections',
      icon: BarChart3,
      color: 'bg-purple-500'
    },
    {
      id: 'development',
      name: 'Player Development',
      description: 'Prospect evaluation & development potential',
      icon: Users,
      color: 'bg-orange-500'
    },
    {
      id: 'business',
      name: 'Business Operations', 
      description: 'Salary cap & financial impact analysis',
      icon: TrendingUp,
      color: 'bg-red-500'
    },
    {
      id: 'gm',
      name: 'Smart GM System',
      description: 'Multi-team perspective analysis',
      icon: Activity,
      color: 'bg-indigo-500'
    }
  ], []);

  // Handle form submission
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedTeam) {
      toast.error("Please select a team first");
      return;
    }

    if (!tradeRequest.trim()) {
      toast.error("Please describe what type of player you're looking for");
      return;
    }

    try {
      const analysis = await tradeAnalysisMutation.mutateAsync({
        request: tradeRequest.trim(),
        team: selectedTeam,
        urgency,
        budget_limit: budgetLimit,
      });
      
      setCurrentAnalysis(analysis);
      toast.analysisStarted();
      
    } catch (error: any) {
      toast.error(error.message || "Failed to start trade analysis");
    }
  }, [selectedTeam, tradeRequest, urgency, budgetLimit, tradeAnalysisMutation]);

  // Handle example click
  const handleExampleClick = (example: string) => {
    setTradeRequest(example);
    // Focus the textarea for better UX
    setTimeout(() => {
      const textarea = document.querySelector('textarea[name="trade-request"]') as HTMLTextAreaElement;
      textarea?.focus();
    }, 100);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + Enter to submit
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        if (!tradeAnalysisMutation.isPending && selectedTeam && tradeRequest.trim()) {
          handleSubmit(e as any);
        }
      }
      
      // Escape to clear
      if (e.key === 'Escape') {
        if (tradeRequest) {
          setTradeRequest('');
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [tradeRequest, selectedTeam, tradeAnalysisMutation.isPending, handleSubmit]);

  return (
    <div className={cn("min-h-screen bg-background", className)}>
      {/* Enhanced Page Header */}
      <PageHeader
        title="Baseball Trade AI"
        description="AI-Powered MLB Trade Analysis with Real-Time Multi-Agent Evaluation"
        sticky
        actions={
          <div className="flex items-center gap-3">
            {/* System Status Indicator */}
            <div className="flex items-center gap-2">
              {isSystemHealthy ? (
                <CheckCircle className="h-4 w-4 text-green-500" aria-label="System operational" />
              ) : (
                <AlertCircle className="h-4 w-4 text-yellow-500" aria-label="System warning" />
              )}
              <span className="text-sm text-muted-foreground">
                {systemHealthQuery.data?.available_teams || 30} Teams
              </span>
            </div>
            
            <Badge variant="outline" className="flex items-center gap-1">
              <Zap className="h-3 w-3" />
              Live AI
            </Badge>
          </div>
        }
      />

      <Container>
        {/* Error Display */}
        {hasError && (
          <Card className="mb-6 border-destructive">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-5 w-5 text-destructive" />
                <h3 className="font-medium text-destructive">Connection Error</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-3">
                Unable to connect to the AI analysis system. Please check your connection and try again.
              </p>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => {
                  systemHealthQuery.refetch();
                  teamsQuery.refetch();
                }}
                loading={systemHealthQuery.isRefetching || teamsQuery.isRefetching}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                Retry Connection
              </Button>
            </CardContent>
          </Card>
        )}

        {/* AI Departments Overview */}
        <section className="mb-8" aria-labelledby="departments-title">
          <h2 id="departments-title" className="text-xl font-semibold text-foreground mb-4">
            AI Front Office Departments
          </h2>
          
          <Grid cols={1} responsive={{ sm: 2, lg: 3 }} gap="md">
            {departments.map((dept) => (
              <Card key={dept.id} className="hover:shadow-card-hover transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className={cn(dept.color, "p-2 rounded-lg")}>
                      <dept.icon className="h-4 w-4 text-white" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-medium text-sm truncate">{dept.name}</h3>
                      <p className="text-xs text-muted-foreground truncate-2">
                        {dept.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </Grid>
        </section>

        {/* Main Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Team Selection Sidebar */}
          <div className="lg:col-span-1">
            <Card className="lg:sticky lg:top-24">
              <CardHeader>
                <CardTitle>Select Your Team</CardTitle>
                <CardDescription>
                  Choose the team you want to find trades for
                </CardDescription>
              </CardHeader>
              
              <CardContent>
                <Field 
                  label="MLB Team"
                  required
                  help="Your team's front office will guide the AI analysis"
                >
                  <TeamDropdown
                    teams={teamsQuery.data?.teams || {}}
                    value={selectedTeam}
                    onValueChange={setSelectedTeam}
                    placeholder="Select a team..."
                    loading={teamsQuery.isLoading}
                    error={teamsQuery.error?.message}
                  />
                </Field>

                {/* Selected Team Details */}
                {selectedTeamData && (
                  <Card className="mt-4 bg-muted/30">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ 
                            backgroundColor: selectedTeamData.colors?.primary || selectedTeamData.primary_color 
                          }}
                          aria-hidden="true"
                        />
                        <h4 className="font-medium">{selectedTeamData.name}</h4>
                      </div>
                      
                      <Stack spacing="xs">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Division:</span>
                          <span className="font-medium">{selectedTeamData.division}</span>
                        </div>
                        
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Budget Level:</span>
                          <Badge 
                            salaryLevel={selectedTeamData.budget_level as any}
                            size="sm"
                          >
                            {selectedTeamData.budget_level}
                          </Badge>
                        </div>
                        
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Window:</span>
                          <Badge
                            teamStatus={selectedTeamData.competitive_window as any}
                            size="sm"
                          >
                            {selectedTeamData.competitive_window?.replace('-', ' ')}
                          </Badge>
                        </div>
                      </Stack>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Trade Request Interface */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Trade Request</CardTitle>
                <CardDescription>
                  Describe what type of player you need in natural language
                </CardDescription>
              </CardHeader>
              
              <CardContent>
                <form onSubmit={handleSubmit}>
                  <Stack spacing="lg">
                    {/* Main Request Input */}
                    <Field
                      label="Player Requirements"
                      required
                      help="Be specific about position, performance metrics, contract situation, or team needs"
                    >
                      <div className="relative">
                        <textarea
                          name="trade-request"
                          value={tradeRequest}
                          onChange={(e) => setTradeRequest(e.target.value)}
                          placeholder="Describe the player you need in natural language..."
                          rows={4}
                          className="form-input resize-none"
                          disabled={tradeAnalysisMutation.isPending}
                          aria-describedby="request-help shortcut-help"
                        />
                        
                        <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
                          <kbd className="px-1 py-0.5 bg-muted border border-border rounded text-xs">
                            ⌘+Enter
                          </kbd> to submit
                        </div>
                      </div>
                    </Field>

                    {/* Example Requests */}
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <Search className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Example Requests</span>
                      </div>
                      
                      <Grid cols={1} responsive={{ sm: 2 }} gap="sm">
                        {exampleRequests.slice(0, 6).map((example, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            size="sm"
                            className="justify-start text-left h-auto p-3 whitespace-normal"
                            onClick={() => handleExampleClick(example)}
                            disabled={tradeAnalysisMutation.isPending}
                          >
                            <span className="text-pretty">"{example}"</span>
                          </Button>
                        ))}
                      </Grid>
                    </div>

                    {/* Advanced Options */}
                    <div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                        className="mb-3"
                        aria-expanded={showAdvancedOptions}
                        aria-controls="advanced-options"
                      >
                        {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options
                      </Button>
                      
                      {showAdvancedOptions && (
                        <div id="advanced-options" className="space-y-4">
                          <Grid cols={1} responsive={{ sm: 2 }} gap="md">
                            {/* Urgency Level */}
                            <Field label="Urgency Level">
                              <select
                                value={urgency}
                                onChange={(e) => setUrgency(e.target.value as any)}
                                className="form-input"
                                disabled={tradeAnalysisMutation.isPending}
                              >
                                <option value="low">Low - Exploring options</option>
                                <option value="medium">Medium - Active interest</option>
                                <option value="high">High - Urgent need</option>
                              </select>
                            </Field>

                            {/* Budget Limit */}
                            <Field
                              label="Budget Limit"
                              help="Maximum salary willing to take on (optional)"
                            >
                              <CurrencyInput
                                value={budgetLimit || ''}
                                onChange={(e) => setBudgetLimit(
                                  e.target.value ? parseFloat(e.target.value) : undefined
                                )}
                                placeholder="25"
                                disabled={tradeAnalysisMutation.isPending}
                              />
                            </Field>
                          </Grid>
                        </div>
                      )}
                    </div>

                    {/* Submit Button */}
                    <Button
                      type="submit"
                      variant="primary"
                      size="lg"
                      loading={tradeAnalysisMutation.isPending}
                      loadingText="Starting AI Analysis..."
                      disabled={!selectedTeam || !tradeRequest.trim()}
                      fullWidth
                      icon={<Zap className="h-5 w-5" />}
                    >
                      Start AI Analysis
                    </Button>

                    {/* Validation Messages */}
                    {!selectedTeam && (
                      <p className="text-center text-sm text-destructive" role="alert">
                        Please select a team first
                      </p>
                    )}
                  </Stack>
                </form>
              </CardContent>
            </Card>

            {/* Analysis Progress */}
            {currentAnalysis && (
              <Card>
                <CardContent className="p-6">
                  <AnalysisProgress
                    steps={defaultAnalysisSteps.map(step => ({
                      ...step,
                      status: step.status as any,
                    }))}
                    overallProgress={45} // This would come from streaming data
                    estimatedTime={90}
                    variant="detailed"
                  />
                </CardContent>
              </Card>
            )}

            {/* Mock Results Display for Design Purposes */}
            {currentAnalysis?.status === 'completed' && (
              <Card>
                <CardHeader>
                  <CardTitle>Trade Analysis Results</CardTitle>
                  <CardDescription>
                    AI-powered recommendations based on your requirements
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <TradeComparison
                    trades={[
                      {
                        id: "1",
                        name: "Power Bat Package",
                        score: 85,
                        teams: ["Yankees", "Guardians"],
                        pros: ["Fills power need", "Good contract value", "Proven performer"],
                        cons: ["High salary commitment"],
                        confidence: 0.82,
                      },
                      {
                        id: "2", 
                        name: "Budget-Friendly Option",
                        score: 72,
                        teams: ["Yankees", "Royals"],
                        pros: ["Low salary impact", "Multiple years of control", "Good clubhouse presence"],
                        cons: ["Lower offensive numbers", "Injury concerns"],
                        confidence: 0.68,
                      },
                    ]}
                  />
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* System Status Footer */}
        <footer className="mt-12" aria-labelledby="system-status-title">
          <Card>
            <CardHeader>
              <CardTitle id="system-status-title">System Status</CardTitle>
              <CardDescription>
                Real-time status of AI analysis capabilities
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <Grid cols={1} responsive={{ md: 3 }} gap="md">
                <StatCard
                  label="Backend Status"
                  value={systemHealthQuery.data?.status || "Unknown"}
                  variant={isSystemHealthy ? "highlighted" : "default"}
                />
                
                <StatCard
                  label="Data Source"
                  value={teamsQuery.data?.source || "Loading..."}
                  description="Live MLB data connection"
                />
                
                <StatCard
                  label="Response Time"
                  value="< 2s"
                  format="time"
                  trend="up"
                  description="Average API response time"
                />
              </Grid>
            </CardContent>
          </Card>
        </footer>
      </Container>
    </div>
  );
}