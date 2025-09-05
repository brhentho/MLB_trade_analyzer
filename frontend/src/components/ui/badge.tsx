/**
 * Enhanced Badge Component System
 * Baseball-themed badges with semantic colors and accessibility
 */

import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 
    | "default" 
    | "secondary" 
    | "outline" 
    | "destructive"
    | "position"
    | "team-status"
    | "performance"
    | "salary"
    | "trade-status";
  size?: "sm" | "default" | "lg";
  position?: "C" | "1B" | "2B" | "3B" | "SS" | "LF" | "CF" | "RF" | "DH" | "SP" | "RP" | "CP";
  teamStatus?: "win-now" | "retool" | "rebuild";
  performance?: "excellent" | "good" | "average" | "poor" | "terrible";
  salaryLevel?: "luxury" | "high" | "medium" | "low" | "rookie";
  tradeStatus?: "pending" | "analyzing" | "completed" | "failed";
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ 
    className, 
    variant = "default", 
    size = "default",
    position,
    teamStatus,
    performance,
    salaryLevel,
    tradeStatus,
    children,
    ...props 
  }, ref) => {
    
    // Determine the actual variant based on semantic props
    let actualVariant = variant;
    let semanticStyles: string[] = [];
    let ariaLabel = "";

    if (position) {
      actualVariant = "position";
      const positionColors = {
        "C": "bg-purple-500 text-white",
        "1B": "bg-blue-500 text-white",
        "2B": "bg-blue-500 text-white", 
        "3B": "bg-blue-500 text-white",
        "SS": "bg-blue-500 text-white",
        "LF": "bg-green-500 text-white",
        "CF": "bg-green-500 text-white",
        "RF": "bg-green-500 text-white",
        "DH": "bg-red-500 text-white",
        "SP": "bg-orange-500 text-white",
        "RP": "bg-orange-600 text-white",
        "CP": "bg-red-600 text-white",
      };
      semanticStyles = [positionColors[position] || "bg-gray-500 text-white"];
      ariaLabel = `Position: ${position}`;
    }

    if (teamStatus) {
      actualVariant = "team-status";
      const statusColors = {
        "win-now": "bg-blue-50 text-blue-700 border-blue-200",
        "retool": "bg-violet-50 text-violet-700 border-violet-200",
        "rebuild": "bg-orange-50 text-orange-700 border-orange-200",
      };
      semanticStyles = [statusColors[teamStatus]];
      ariaLabel = `Team status: ${teamStatus.replace('-', ' ')}`;
    }

    if (performance) {
      actualVariant = "performance";
      const performanceColors = {
        "excellent": "bg-green-50 text-green-700 border-green-200",
        "good": "bg-lime-50 text-lime-700 border-lime-200",
        "average": "bg-yellow-50 text-yellow-700 border-yellow-200",
        "poor": "bg-red-50 text-red-700 border-red-200",
        "terrible": "bg-red-100 text-red-800 border-red-300",
      };
      semanticStyles = [performanceColors[performance]];
      ariaLabel = `Performance: ${performance}`;
    }

    if (salaryLevel) {
      actualVariant = "salary";
      const salaryColors = {
        "luxury": "bg-red-50 text-red-700 border-red-200",
        "high": "bg-orange-50 text-orange-700 border-orange-200",
        "medium": "bg-yellow-50 text-yellow-700 border-yellow-200",
        "low": "bg-green-50 text-green-700 border-green-200",
        "rookie": "bg-emerald-50 text-emerald-700 border-emerald-200",
      };
      semanticStyles = [salaryColors[salaryLevel]];
      ariaLabel = `Salary level: ${salaryLevel}`;
    }

    if (tradeStatus) {
      actualVariant = "trade-status";
      const statusColors = {
        "pending": "trade-status-pending",
        "analyzing": "trade-status-analyzing",
        "completed": "trade-status-completed",
        "failed": "trade-status-failed",
      };
      semanticStyles = [statusColors[tradeStatus]];
      ariaLabel = `Trade status: ${tradeStatus}`;
    }

    const baseStyles = [
      "inline-flex items-center gap-1 rounded-full font-medium",
      "border transition-all duration-200",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1"
    ];

    const variants = {
      default: [
        "bg-primary text-primary-foreground border-primary",
        "hover:bg-primary/80"
      ],
      secondary: [
        "bg-secondary text-secondary-foreground border-secondary",
        "hover:bg-secondary/80"
      ],
      outline: [
        "border-border bg-transparent text-foreground",
        "hover:bg-muted"
      ],
      destructive: [
        "bg-destructive text-destructive-foreground border-destructive",
        "hover:bg-destructive/80"
      ],
      position: semanticStyles,
      "team-status": ["border", ...semanticStyles],
      performance: ["border", ...semanticStyles],
      salary: ["border", ...semanticStyles],
      "trade-status": ["border", ...semanticStyles],
    };

    const sizes = {
      sm: "px-2 py-0.5 text-xs h-5",
      default: "px-2.5 py-1 text-xs h-6",
      lg: "px-3 py-1.5 text-sm h-7",
    };

    return (
      <span
        ref={ref}
        className={cn(
          baseStyles,
          variants[actualVariant],
          sizes[size],
          className
        )}
        aria-label={ariaLabel || undefined}
        {...props}
      >
        {children}
      </span>
    );
  }
);
Badge.displayName = "Badge";

// Specialized badge components

interface PositionBadgeProps {
  position: BadgeProps['position'];
  size?: BadgeProps['size'];
  className?: string;
}

const PositionBadge: React.FC<PositionBadgeProps> = ({ 
  position, 
  size = "default", 
  className 
}) => {
  if (!position) return null;

  const positionNames = {
    "C": "Catcher",
    "1B": "First Base",
    "2B": "Second Base", 
    "3B": "Third Base",
    "SS": "Shortstop",
    "LF": "Left Field",
    "CF": "Center Field",
    "RF": "Right Field",
    "DH": "Designated Hitter",
    "SP": "Starting Pitcher",
    "RP": "Relief Pitcher",
    "CP": "Closer",
  };

  return (
    <Badge
      position={position}
      size={size}
      className={className}
      aria-label={`Position: ${positionNames[position] || position}`}
    >
      {position}
    </Badge>
  );
};

interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'injured' | 'suspended' | 'trade-block';
  size?: BadgeProps['size'];
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "default",
  className
}) => {
  const statusConfig = {
    active: { variant: "default" as const, text: "Active" },
    inactive: { variant: "outline" as const, text: "Inactive" },
    injured: { variant: "destructive" as const, text: "Injured" },
    suspended: { variant: "destructive" as const, text: "Suspended" },
    "trade-block": { variant: "secondary" as const, text: "Available" },
  };

  const config = statusConfig[status];

  return (
    <Badge
      variant={config.variant}
      size={size}
      className={className}
      aria-label={`Player status: ${config.text}`}
    >
      {config.text}
    </Badge>
  );
};

export {
  Badge,
  PositionBadge,
  StatusBadge,
  type BadgeProps,
  type PositionBadgeProps,
  type StatusBadgeProps,
};