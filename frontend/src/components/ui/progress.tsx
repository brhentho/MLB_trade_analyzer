/**
 * Enhanced Progress Component System
 * Baseball Trade AI analysis progress indicators with accessibility
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  Zap,
  Search,
  BarChart3,
  Users,
  Building2,
  TrendingUp,
  Activity,
  Shield
} from "lucide-react";
import { Badge } from "./badge";

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0-100
  variant?: "default" | "success" | "warning" | "error" | "baseball";
  size?: "sm" | "default" | "lg";
  showValue?: boolean;
  animated?: boolean;
  indeterminate?: boolean;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ 
    className, 
    value, 
    variant = "default",
    size = "default",
    showValue = false,
    animated = true,
    indeterminate = false,
    ...props 
  }, ref) => {
    const clampedValue = Math.min(100, Math.max(0, value));
    
    const variants = {
      default: "bg-primary",
      success: "bg-green-500",
      warning: "bg-yellow-500",
      error: "bg-destructive",
      baseball: "bg-gradient-to-r from-green-500 to-blue-500",
    };

    const sizes = {
      sm: "h-1",
      default: "h-2",
      lg: "h-3",
    };

    return (
      <div
        ref={ref}
        className={cn("w-full", className)}
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Progress: ${Math.round(clampedValue)}%`}
        {...props}
      >
        <div className={cn(
          "w-full bg-muted rounded-full overflow-hidden",
          sizes[size]
        )}>
          <div 
            className={cn(
              variants[variant],
              "h-full transition-all duration-500 ease-out rounded-full",
              animated && "animate-pulse",
              indeterminate && "animate-progress-bar"
            )}
            style={{ 
              width: indeterminate ? "100%" : `${clampedValue}%`,
              transform: indeterminate ? "translateX(-100%)" : undefined,
            }}
          />
        </div>
        
        {showValue && (
          <div className="mt-1 text-right text-xs text-muted-foreground">
            {Math.round(clampedValue)}%
          </div>
        )}
      </div>
    );
  }
);
Progress.displayName = "Progress";

// AI Analysis Step Progress Component
interface AnalysisStep {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  status: "pending" | "in_progress" | "completed" | "error";
  duration?: number;
  startTime?: Date;
  endTime?: Date;
}

interface AnalysisProgressProps {
  steps: AnalysisStep[];
  currentStep?: string;
  overallProgress?: number;
  estimatedTime?: number;
  variant?: "default" | "compact" | "detailed";
  onStepClick?: (stepId: string) => void;
}

const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  steps,
  currentStep,
  overallProgress,
  estimatedTime,
  variant = "default",
  onStepClick,
}) => {
  const completedSteps = steps.filter(step => step.status === "completed").length;
  const totalSteps = steps.length;
  const progressValue = overallProgress || (completedSteps / totalSteps) * 100;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" aria-label="Completed" />;
      case "in_progress":
        return (
          <div 
            className="h-5 w-5 border-2 border-primary border-t-transparent rounded-full animate-spin" 
            aria-label="In progress"
          />
        );
      case "error":
        return <AlertCircle className="h-5 w-5 text-destructive" aria-label="Error" />;
      default:
        return <Clock className="h-5 w-5 text-muted-foreground" aria-label="Pending" />;
    }
  };

  const getStatusStyles = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-50 border-green-200 text-green-800";
      case "in_progress":
        return "bg-blue-50 border-blue-200 text-blue-800 ring-2 ring-blue-100";
      case "error":
        return "bg-red-50 border-red-200 text-red-800";
      default:
        return "bg-muted border-border text-muted-foreground";
    }
  };

  if (variant === "compact") {
    return (
      <div className="space-y-3" role="progressbar" aria-label="Analysis progress">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Analysis Progress</span>
          <span className="text-sm text-muted-foreground">
            {completedSteps}/{totalSteps} complete
          </span>
        </div>
        
        <Progress 
          value={progressValue} 
          variant="baseball" 
          showValue 
          animated={currentStep !== undefined}
        />
        
        {estimatedTime && (
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Est. {Math.ceil(estimatedTime / 60)} minutes remaining
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4" role="group" aria-label="AI Analysis Progress">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            AI Front Office Analysis
          </h3>
          <p className="text-sm text-muted-foreground">
            Multi-agent evaluation in progress
          </p>
        </div>
        
        <div className="text-right">
          <div className="text-2xl font-bold text-primary">
            {Math.round(progressValue)}%
          </div>
          <div className="text-sm text-muted-foreground">
            {completedSteps} of {totalSteps} departments
          </div>
        </div>
      </div>

      {/* Overall Progress */}
      <Progress 
        value={progressValue} 
        variant="baseball" 
        size="lg"
        animated={currentStep !== undefined}
      />

      {/* Time Estimation */}
      {estimatedTime && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>Estimated time remaining: {Math.ceil(estimatedTime / 60)} minutes</span>
        </div>
      )}

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step, index) => {
          const isClickable = onStepClick && (step.status === "completed" || step.status === "error");
          
          return (
            <div
              key={step.id}
              className={cn(
                "p-4 rounded-lg border transition-all duration-300",
                getStatusStyles(step.status),
                isClickable && "cursor-pointer hover:shadow-sm",
                step.status === "in_progress" && "animate-fade-in"
              )}
              onClick={isClickable ? () => onStepClick(step.id) : undefined}
              role={isClickable ? "button" : undefined}
              tabIndex={isClickable ? 0 : undefined}
              onKeyDown={isClickable ? (e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onStepClick(step.id);
                }
              } : undefined}
              aria-label={`${step.name}: ${step.status.replace('_', ' ')}`}
            >
              <div className="flex items-center gap-4">
                <div className="flex-shrink-0">
                  {getStatusIcon(step.status)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <step.icon className="h-4 w-4" aria-hidden="true" />
                    <h4 className="font-medium truncate">
                      {step.name}
                    </h4>
                    {step.status === "in_progress" && (
                      <Badge variant="outline" size="sm">
                        Active
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm opacity-90 mt-1 text-pretty">
                    {step.description}
                  </p>
                  
                  {step.duration && variant === "detailed" && (
                    <p className="text-xs mt-1 opacity-75">
                      Duration: {Math.round(step.duration / 1000)}s
                    </p>
                  )}
                </div>
                
                <div className="flex-shrink-0 text-right">
                  {step.status === "completed" && (
                    <Badge variant="default" size="sm">
                      Done
                    </Badge>
                  )}
                  {step.status === "in_progress" && (
                    <Badge variant="secondary" size="sm">
                      Working...
                    </Badge>
                  )}
                  {step.status === "error" && (
                    <Badge variant="destructive" size="sm">
                      Failed
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Default analysis steps for baseball trade AI
export const defaultAnalysisSteps: AnalysisStep[] = [
  {
    id: "coordination",
    name: "Front Office Coordination",
    description: "Orchestrating multi-agent analysis workflow",
    icon: Building2,
    status: "pending",
  },
  {
    id: "scouting", 
    name: "Scouting Department",
    description: "Player evaluation and scouting insights",
    icon: Search,
    status: "pending",
  },
  {
    id: "analytics",
    name: "Analytics Department", 
    description: "Statistical analysis and performance projections",
    icon: BarChart3,
    status: "pending",
  },
  {
    id: "development",
    name: "Player Development",
    description: "Prospect evaluation and development potential",
    icon: Users,
    status: "pending",
  },
  {
    id: "business",
    name: "Business Operations",
    description: "Salary cap and financial impact analysis",
    icon: TrendingUp,
    status: "pending",
  },
  {
    id: "gm_perspective",
    name: "GM Perspective",
    description: "Multi-team strategic evaluation",
    icon: Activity,
    status: "pending",
  },
  {
    id: "compliance",
    name: "Commissioner Review",
    description: "MLB rule compliance verification",
    icon: Shield,
    status: "pending",
  },
];

export {
  Progress,
  AnalysisProgress,
  type ProgressProps,
  type AnalysisProgressProps,
  type AnalysisStep,
};