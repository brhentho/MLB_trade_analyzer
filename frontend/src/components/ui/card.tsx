/**
 * Enhanced Card Component System
 * Baseball-themed card layouts with accessibility and responsive design
 */

import * as React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "outline" | "filled" | "elevated" | "glass" | "baseball";
  interactive?: boolean;
  loading?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", interactive = false, loading = false, children, ...props }, ref) => {
    const variants = {
      default: "card",
      outline: "card border-2 border-statslugger-orange-primary/30",
      filled: "card bg-statslugger-navy-primary",
      elevated: "card shadow-lg shadow-black/25",
      glass: "glass-effect rounded-lg border",
      baseball: "card border-2 border-statslugger-orange-primary/20 bg-gradient-to-br from-statslugger-navy-deep to-statslugger-navy-primary",
    };

    return (
      <div
        ref={ref}
        className={cn(
          variants[variant],
          interactive && [
            "cursor-pointer transition-all duration-200",
            "hover:shadow-card-hover hover:-translate-y-0.5",
            "active:scale-[0.99]"
          ],
          loading && "animate-pulse",
          className
        )}
        role={interactive ? "button" : undefined}
        tabIndex={interactive ? 0 : undefined}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("card-header", className)} {...props} />
  )
);
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, children, ...props }, ref) => (
    <h3 
      ref={ref} 
      className={cn("card-title text-balance", className)} 
      {...props}
    >
      {children}
    </h3>
  )
);
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => (
    <p 
      ref={ref} 
      className={cn("card-description text-pretty", className)} 
      {...props}
    >
      {children}
    </p>
  )
);
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("card-content", className)} {...props} />
  )
);
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("card-footer", className)} {...props} />
  )
);
CardFooter.displayName = "CardFooter";

// Baseball-specific card components

interface PlayerCardProps extends CardProps {
  player?: {
    name: string;
    position: string;
    team: string;
    jersey?: string;
  };
  stats?: Record<string, number | string>;
  compact?: boolean;
}

const PlayerCard = React.forwardRef<HTMLDivElement, PlayerCardProps>(
  ({ player, stats, compact = false, className, children, ...props }, ref) => {
    if (!player) return null;

    return (
      <Card
        ref={ref}
        variant="default"
        className={cn(
          "player-card",
          compact ? "p-3" : "p-4",
          className
        )}
        {...props}
      >
        <CardHeader className={compact ? "p-0 pb-2" : "p-0 pb-3"}>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="position-badge">
                {player.position}
              </div>
              {player.jersey && (
                <span className="text-xs text-muted-foreground">
                  #{player.jersey}
                </span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <CardTitle className={cn(
                compact ? "text-base" : "text-lg",
                "truncate"
              )}>
                {player.name}
              </CardTitle>
              <CardDescription className="truncate">
                {player.team}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        
        {(stats || children) && (
          <CardContent className={compact ? "p-0 pt-2" : "p-0 pt-3"}>
            {stats && (
              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(stats).map(([key, value]) => (
                  <div key={key} className="stat-card p-2">
                    <div className="stat-label">{key}</div>
                    <div className="stat-value text-sm">{value}</div>
                  </div>
                ))}
              </div>
            )}
            {children}
          </CardContent>
        )}
      </Card>
    );
  }
);
PlayerCard.displayName = "PlayerCard";

interface TeamCardProps extends CardProps {
  team?: {
    name: string;
    city: string;
    division: string;
    colors?: { primary: string; secondary: string };
  };
  stats?: Record<string, number | string>;
}

const TeamCard = React.forwardRef<HTMLDivElement, TeamCardProps>(
  ({ team, stats, className, children, ...props }, ref) => {
    if (!team) return null;

    return (
      <Card
        ref={ref}
        variant="default"
        className={cn("overflow-hidden", className)}
        {...props}
      >
        {/* Team header with colors */}
        <div 
          className="h-2"
          style={{
            background: team.colors?.primary || 'var(--primary)',
          }}
        />
        
        <CardHeader>
          <div className="flex items-center gap-3">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: team.colors?.primary || 'var(--primary)' }}
            />
            <div>
              <CardTitle>{team.name}</CardTitle>
              <CardDescription>{team.city} • {team.division}</CardDescription>
            </div>
          </div>
        </CardHeader>
        
        {(stats || children) && (
          <CardContent>
            {stats && (
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(stats).map(([key, value]) => (
                  <div key={key} className="text-center">
                    <div className="text-lg font-bold">{value}</div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wide">
                      {key}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {children}
          </CardContent>
        )}
      </Card>
    );
  }
);
TeamCard.displayName = "TeamCard";

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  PlayerCard,
  TeamCard,
  type CardProps,
  type PlayerCardProps,
  type TeamCardProps,
};