/**
 * Enhanced Data Visualization Components
 * Baseball statistics and trade analysis visualizations with accessibility
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, Info } from "lucide-react";
import { Badge } from "./badge";

// Stat card component
interface StatCardProps {
  label: string;
  value: string | number;
  change?: {
    value: number;
    type: "increase" | "decrease" | "neutral";
    period?: string;
  };
  trend?: "up" | "down" | "neutral";
  format?: "number" | "currency" | "percentage" | "time";
  size?: "sm" | "default" | "lg";
  variant?: "default" | "highlighted" | "minimal";
  className?: string;
  description?: string;
}

const StatCard = React.forwardRef<HTMLDivElement, StatCardProps>(
  ({ 
    label,
    value,
    change,
    trend,
    format = "number",
    size = "default",
    variant = "default",
    className,
    description,
    ...props
  }, ref) => {
    
    // Format the value based on type
    const formatValue = (val: string | number) => {
      if (typeof val === "string") return val;
      
      switch (format) {
        case "currency":
          return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
          }).format(val);
        case "percentage":
          return `${(val * 100).toFixed(1)}%`;
        case "time":
          return `${Math.round(val)}s`;
        default:
          return val.toLocaleString();
      }
    };

    const getTrendIcon = () => {
      if (!trend) return null;
      
      switch (trend) {
        case "up":
          return <TrendingUp className="h-4 w-4 text-green-500" aria-label="Trending up" />;
        case "down":
          return <TrendingDown className="h-4 w-4 text-red-500" aria-label="Trending down" />;
        default:
          return <Minus className="h-4 w-4 text-gray-500" aria-label="No change" />;
      }
    };

    const getChangeStyles = () => {
      if (!change) return "";
      
      switch (change.type) {
        case "increase":
          return "text-green-600";
        case "decrease":
          return "text-red-600";
        default:
          return "text-gray-600";
      }
    };

    const sizes = {
      sm: {
        card: "p-3",
        value: "text-lg",
        label: "text-xs",
      },
      default: {
        card: "p-4",
        value: "text-2xl",
        label: "text-sm",
      },
      lg: {
        card: "p-6",
        value: "text-3xl", 
        label: "text-base",
      },
    };

    const variants = {
      default: "stat-card",
      highlighted: "stat-card bg-primary/5 border-primary/20",
      minimal: "bg-transparent border-none p-0",
    };

    return (
      <div
        ref={ref}
        className={cn(
          variants[variant],
          sizes[size].card,
          className
        )}
        role="region"
        aria-label={`${label}: ${formatValue(value)}`}
        {...props}
      >
        <div className="flex items-center justify-between mb-1">
          <p className={cn(
            "stat-label font-medium",
            sizes[size].label
          )}>
            {label}
          </p>
          
          {getTrendIcon()}
        </div>
        
        <div className="flex items-baseline gap-2">
          <p className={cn(
            "stat-value font-bold",
            sizes[size].value
          )}>
            {formatValue(value)}
          </p>
          
          {change && (
            <span className={cn(
              "text-xs font-medium flex items-center gap-1",
              getChangeStyles()
            )}>
              {change.type === "increase" && "+"}
              {change.value}
              {change.period && ` ${change.period}`}
            </span>
          )}
        </div>
        
        {description && (
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        )}
      </div>
    );
  }
);
StatCard.displayName = "StatCard";

// Performance meter component
interface PerformanceMeterProps {
  value: number; // 0-100
  label: string;
  thresholds?: {
    excellent: number;
    good: number;
    average: number;
    poor: number;
  };
  showLabel?: boolean;
  size?: "sm" | "default" | "lg";
  className?: string;
}

const PerformanceMeter: React.FC<PerformanceMeterProps> = ({
  value,
  label,
  thresholds = { excellent: 80, good: 60, average: 40, poor: 20 },
  showLabel = true,
  size = "default",
  className,
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));
  
  const getPerformanceLevel = () => {
    if (clampedValue >= thresholds.excellent) return "excellent";
    if (clampedValue >= thresholds.good) return "good";
    if (clampedValue >= thresholds.average) return "average";
    if (clampedValue >= thresholds.poor) return "poor";
    return "terrible";
  };

  const performanceLevel = getPerformanceLevel();

  const levelColors = {
    excellent: "text-green-600 bg-green-500",
    good: "text-lime-600 bg-lime-500",
    average: "text-yellow-600 bg-yellow-500",
    poor: "text-red-600 bg-red-500",
    terrible: "text-red-800 bg-red-600",
  };

  const sizes = {
    sm: "h-1",
    default: "h-2",
    lg: "h-3",
  };

  return (
    <div className={cn("space-y-2", className)}>
      {showLabel && (
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">{label}</span>
          <span className={levelColors[performanceLevel].split(" ")[0]}>
            {Math.round(clampedValue)}%
          </span>
        </div>
      )}
      
      <div className={cn("w-full bg-muted rounded-full", sizes[size])}>
        <div 
          className={cn(
            "h-full rounded-full transition-all duration-500 ease-out",
            levelColors[performanceLevel].split(" ")[1]
          )}
          style={{ width: `${clampedValue}%` }}
          role="progressbar"
          aria-valuenow={clampedValue}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${label}: ${performanceLevel} performance at ${Math.round(clampedValue)}%`}
        />
      </div>
    </div>
  );
};

// Trade comparison component
interface TradeComparisonProps {
  trades: Array<{
    id: string;
    name: string;
    score: number;
    teams: string[];
    pros: string[];
    cons: string[];
    confidence: number;
  }>;
  onTradeSelect?: (tradeId: string) => void;
  className?: string;
}

const TradeComparison: React.FC<TradeComparisonProps> = ({
  trades,
  onTradeSelect,
  className,
}) => {
  const [selectedTrade, setSelectedTrade] = React.useState<string | null>(null);

  const handleTradeClick = (tradeId: string) => {
    setSelectedTrade(tradeId);
    onTradeSelect?.(tradeId);
  };

  return (
    <div className={cn("space-y-4", className)}>
      <h3 className="text-lg font-semibold mb-4">Trade Options Comparison</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {trades.map((trade, index) => (
          <div
            key={trade.id}
            className={cn(
              "card p-4 cursor-pointer transition-all duration-200",
              "hover:shadow-card-hover hover:-translate-y-1",
              selectedTrade === trade.id && "ring-2 ring-primary"
            )}
            onClick={() => handleTradeClick(trade.id)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleTradeClick(trade.id);
              }
            }}
            aria-label={`Trade option ${index + 1}: ${trade.name}`}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-medium truncate">{trade.name}</h4>
                <p className="text-sm text-muted-foreground">
                  {trade.teams.join(" ↔ ")}
                </p>
              </div>
              
              <div className="text-right">
                <div className="text-lg font-bold text-primary">
                  {Math.round(trade.score)}
                </div>
                <Badge 
                  performance={
                    trade.confidence >= 0.8 ? "excellent" :
                    trade.confidence >= 0.6 ? "good" :
                    trade.confidence >= 0.4 ? "average" : "poor"
                  }
                  size="sm"
                >
                  {Math.round(trade.confidence * 100)}%
                </Badge>
              </div>
            </div>

            {/* Performance meter */}
            <PerformanceMeter
              value={trade.score}
              label="Trade Score"
              size="sm"
              showLabel={false}
            />

            {/* Pros and Cons */}
            <div className="mt-3 space-y-2">
              {trade.pros.slice(0, 2).map((pro, i) => (
                <p key={i} className="text-xs text-green-700 flex items-start gap-1">
                  <span className="text-green-500 shrink-0">+</span>
                  <span className="text-pretty">{pro}</span>
                </p>
              ))}
              
              {trade.cons.slice(0, 1).map((con, i) => (
                <p key={i} className="text-xs text-red-700 flex items-start gap-1">
                  <span className="text-red-500 shrink-0">−</span>
                  <span className="text-pretty">{con}</span>
                </p>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Roster visualization component
interface RosterVisualizationProps {
  roster: Array<{
    id: string;
    name: string;
    position: string;
    salary?: number;
    performance?: number;
    availability?: "available" | "unavailable" | "maybe";
  }>;
  interactive?: boolean;
  onPlayerClick?: (playerId: string) => void;
  className?: string;
}

const RosterVisualization: React.FC<RosterVisualizationProps> = ({
  roster,
  interactive = false,
  onPlayerClick,
  className,
}) => {
  const positionGroups = React.useMemo(() => {
    return roster.reduce((groups, player) => {
      const group = player.position;
      if (!groups[group]) groups[group] = [];
      groups[group].push(player);
      return groups;
    }, {} as Record<string, typeof roster>);
  }, [roster]);

  const getAvailabilityColor = (availability: string) => {
    switch (availability) {
      case "available":
        return "border-green-500 bg-green-50";
      case "maybe":
        return "border-yellow-500 bg-yellow-50";
      default:
        return "border-red-500 bg-red-50";
    }
  };

  return (
    <div className={cn("space-y-6", className)}>
      {Object.entries(positionGroups).map(([position, players]) => (
        <div key={position}>
          <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wider mb-3">
            {position} ({players.length})
          </h4>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {players.map((player) => (
              <div
                key={player.id}
                className={cn(
                  "p-3 rounded-lg border transition-all duration-200",
                  player.availability && getAvailabilityColor(player.availability),
                  interactive && [
                    "cursor-pointer hover:shadow-sm hover:-translate-y-0.5",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1"
                  ]
                )}
                onClick={interactive ? () => onPlayerClick?.(player.id) : undefined}
                role={interactive ? "button" : undefined}
                tabIndex={interactive ? 0 : undefined}
                onKeyDown={interactive ? (e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onPlayerClick?.(player.id);
                  }
                } : undefined}
                aria-label={`${player.name}, ${player.position}${player.availability ? `, ${player.availability}` : ""}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h5 className="font-medium text-sm truncate">{player.name}</h5>
                  {player.availability && (
                    <Badge 
                      variant={
                        player.availability === "available" ? "default" :
                        player.availability === "maybe" ? "secondary" :
                        "destructive"
                      }
                      size="sm"
                    >
                      {player.availability}
                    </Badge>
                  )}
                </div>
                
                {player.performance !== undefined && (
                  <PerformanceMeter
                    value={player.performance}
                    label="Performance"
                    size="sm"
                    showLabel={false}
                  />
                )}
                
                {player.salary && (
                  <p className="text-xs text-muted-foreground mt-2">
                    ${(player.salary / 1000000).toFixed(1)}M
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

// Trade impact visualization
interface TradeImpactProps {
  beforeStats: Record<string, number>;
  afterStats: Record<string, number>;
  categories: Array<{
    key: string;
    label: string;
    format?: "number" | "currency" | "percentage";
    description?: string;
  }>;
  className?: string;
}

const TradeImpact: React.FC<TradeImpactProps> = ({
  beforeStats,
  afterStats,
  categories,
  className,
}) => {
  return (
    <div className={cn("space-y-4", className)}>
      <h3 className="text-lg font-semibold">Trade Impact Analysis</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {categories.map((category) => {
          const before = beforeStats[category.key] || 0;
          const after = afterStats[category.key] || 0;
          const change = after - before;
          const changePercent = before !== 0 ? (change / before) * 100 : 0;
          
          return (
            <div key={category.key} className="stat-card p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-sm">{category.label}</h4>
                {category.description && (
                  <button
                    className="text-muted-foreground hover:text-foreground transition-colors"
                    aria-label={`Information about ${category.label}`}
                    title={category.description}
                  >
                    <Info className="h-3 w-3" />
                  </button>
                )}
              </div>
              
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <p className="text-sm text-muted-foreground">Before</p>
                  <p className="font-semibold">{before.toLocaleString()}</p>
                </div>
                
                <div>
                  <p className="text-sm text-muted-foreground">After</p>
                  <p className="font-semibold">{after.toLocaleString()}</p>
                </div>
                
                <div>
                  <p className="text-sm text-muted-foreground">Change</p>
                  <div className={cn(
                    "font-semibold flex items-center justify-center gap-1",
                    change > 0 ? "stat-change-positive" : 
                    change < 0 ? "stat-change-negative" : 
                    "text-gray-600"
                  )}>
                    {change > 0 && <TrendingUp className="h-3 w-3" />}
                    {change < 0 && <TrendingDown className="h-3 w-3" />}
                    <span>
                      {change > 0 && "+"}
                      {changePercent.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Simple chart component for basic visualizations
interface SimpleChartProps {
  data: Array<{
    label: string;
    value: number;
    color?: string;
  }>;
  type?: "bar" | "line" | "area";
  height?: number;
  showValues?: boolean;
  className?: string;
}

const SimpleChart: React.FC<SimpleChartProps> = ({
  data,
  type = "bar",
  height = 200,
  showValues = false,
  className,
}) => {
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <div className={cn("space-y-3", className)}>
      <div 
        className="flex items-end gap-2 p-4 bg-muted/20 rounded-lg"
        style={{ height }}
        role="img"
        aria-label="Data visualization chart"
      >
        {data.map((item, index) => {
          const heightPercent = (item.value / maxValue) * 100;
          
          return (
            <div key={index} className="flex-1 flex flex-col items-center gap-1">
              <div 
                className={cn(
                  "w-full rounded-t transition-all duration-500",
                  item.color || "bg-primary"
                )}
                style={{ 
                  height: `${heightPercent}%`,
                  minHeight: "2px"
                }}
                aria-label={`${item.label}: ${item.value}`}
              />
              
              {showValues && (
                <span className="text-xs font-medium">
                  {item.value}
                </span>
              )}
              
              <span className="text-xs text-muted-foreground text-center">
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export {
  StatCard,
  PerformanceMeter,
  TradeComparison,
  RosterVisualization,
  TradeImpact,
  SimpleChart,
  type StatCardProps,
  type PerformanceMeterProps,
  type TradeComparisonProps,
  type RosterVisualizationProps,
  type TradeImpactProps,
  type SimpleChartProps,
};