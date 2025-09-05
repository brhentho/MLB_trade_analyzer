/**
 * Enhanced Button Component
 * Follows design system patterns with baseball-themed variants
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { LoadingSpinner } from "./loading-states";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 
    | "primary" 
    | "secondary" 
    | "outline" 
    | "ghost" 
    | "destructive"
    | "baseball"
    | "team-primary"
    | "team-secondary";
  size?: "sm" | "default" | "lg" | "icon" | "touch";
  loading?: boolean;
  loadingText?: string;
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  fullWidth?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant = "primary", 
    size = "default", 
    loading = false,
    loadingText,
    icon,
    iconPosition = "left",
    fullWidth = false,
    children,
    disabled,
    ...props 
  }, ref) => {
    const baseStyles = [
      "inline-flex items-center justify-center gap-2 rounded-md font-medium",
      "transition-all duration-200 ease-out",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
      "disabled:pointer-events-none disabled:opacity-50",
      "touch-target", // Ensure proper touch targets
      fullWidth && "w-full"
    ];

    const variants = {
      primary: [
        "bg-primary text-primary-foreground shadow-sm",
        "hover:bg-primary/90 hover:shadow-md",
        "focus-visible:ring-primary",
        "active:scale-[0.98]"
      ],
      secondary: [
        "bg-secondary text-secondary-foreground shadow-sm",
        "hover:bg-secondary/80 hover:shadow-md",
        "focus-visible:ring-secondary",
        "active:scale-[0.98]"
      ],
      outline: [
        "border border-border bg-background text-foreground",
        "hover:bg-muted hover:shadow-sm",
        "focus-visible:ring-ring",
        "active:scale-[0.98]"
      ],
      ghost: [
        "text-foreground",
        "hover:bg-muted hover:shadow-sm",
        "focus-visible:ring-ring",
        "active:scale-[0.98]"
      ],
      destructive: [
        "bg-destructive text-destructive-foreground shadow-sm",
        "hover:bg-destructive/90 hover:shadow-md",
        "focus-visible:ring-destructive",
        "active:scale-[0.98]"
      ],
      baseball: [
        "bg-gradient-to-r from-baseball-field-green to-emerald-600 text-white shadow-md",
        "hover:from-green-600 hover:to-emerald-700 hover:shadow-lg",
        "focus-visible:ring-emerald-500",
        "active:scale-[0.98]"
      ],
      "team-primary": [
        "bg-team-win-now text-white shadow-md",
        "hover:bg-blue-700 hover:shadow-lg",
        "focus-visible:ring-blue-500",
        "active:scale-[0.98]"
      ],
      "team-secondary": [
        "bg-team-retool text-white shadow-md",
        "hover:bg-violet-700 hover:shadow-lg",
        "focus-visible:ring-violet-500",
        "active:scale-[0.98]"
      ],
    };

    const sizes = {
      sm: "h-8 px-3 text-xs",
      default: "h-10 px-4 text-sm",
      lg: "h-12 px-6 text-base",
      icon: "h-10 w-10 p-0",
      touch: "h-12 px-6 text-base min-w-[44px]", // Mobile-optimized
    };

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          className
        )}
        disabled={loading || disabled}
        aria-busy={loading}
        aria-describedby={loading && loadingText ? "button-loading-text" : undefined}
        {...props}
      >
        {loading && (
          <LoadingSpinner 
            size={size === "sm" ? "sm" : "default"} 
            className="shrink-0" 
          />
        )}
        
        {!loading && icon && iconPosition === "left" && (
          <span className="shrink-0" aria-hidden="true">
            {icon}
          </span>
        )}
        
        <span className={cn(
          "flex-1",
          loading && "sr-only"
        )}>
          {loading ? (loadingText || "Loading...") : children}
        </span>
        
        {!loading && icon && iconPosition === "right" && (
          <span className="shrink-0" aria-hidden="true">
            {icon}
          </span>
        )}
        
        {loading && loadingText && (
          <span id="button-loading-text" className="sr-only">
            {loadingText}
          </span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button, type ButtonProps };