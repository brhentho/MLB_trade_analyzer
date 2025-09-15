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
        "bg-gradient-to-r from-statslugger-orange-primary to-statslugger-orange-secondary text-white shadow-md",
        "hover:from-statslugger-orange-secondary hover:to-statslugger-orange-dark hover:shadow-lg",
        "focus-visible:ring-statslugger-orange-primary focus-visible:ring-offset-statslugger-navy-primary",
        "active:scale-[0.98]"
      ],
      secondary: [
        "bg-statslugger-navy-primary border border-statslugger-navy-border text-statslugger-text-secondary shadow-sm",
        "hover:bg-statslugger-navy-border hover:text-statslugger-text-primary hover:shadow-md",
        "focus-visible:ring-statslugger-orange-primary focus-visible:ring-offset-statslugger-navy-primary",
        "active:scale-[0.98]"
      ],
      outline: [
        "border-2 border-statslugger-orange-primary bg-transparent text-statslugger-orange-primary",
        "hover:bg-statslugger-orange-primary hover:text-white hover:shadow-md",
        "focus-visible:ring-statslugger-orange-primary focus-visible:ring-offset-statslugger-navy-primary",
        "active:scale-[0.98]"
      ],
      ghost: [
        "text-statslugger-text-primary",
        "hover:bg-statslugger-navy-primary hover:text-statslugger-orange-primary hover:shadow-sm",
        "focus-visible:ring-statslugger-orange-primary focus-visible:ring-offset-statslugger-navy-primary",
        "active:scale-[0.98]"
      ],
      destructive: [
        "bg-red-600 text-white shadow-sm",
        "hover:bg-red-700 hover:shadow-md",
        "focus-visible:ring-red-500 focus-visible:ring-offset-statslugger-navy-primary",
        "active:scale-[0.98]"
      ],
      baseball: [
        "bg-gradient-to-r from-statslugger-orange-primary via-statslugger-orange-secondary to-statslugger-orange-primary text-white shadow-md",
        "hover:shadow-lg hover:from-statslugger-orange-secondary hover:to-statslugger-orange-dark",
        "focus-visible:ring-statslugger-orange-primary focus-visible:ring-offset-statslugger-navy-primary",
        "active:scale-[0.98]"
      ],
      "team-primary": [
        "bg-gradient-to-r from-statslugger-orange-primary to-yellow-500 text-white shadow-md",
        "hover:from-statslugger-orange-secondary hover:to-yellow-600 hover:shadow-lg",
        "focus-visible:ring-statslugger-orange-primary focus-visible:ring-offset-statslugger-navy-primary",
        "active:scale-[0.98]"
      ],
      "team-secondary": [
        "bg-gradient-to-r from-purple-600 to-statslugger-orange-secondary text-white shadow-md",
        "hover:from-purple-700 hover:to-statslugger-orange-dark hover:shadow-lg",
        "focus-visible:ring-purple-500 focus-visible:ring-offset-statslugger-navy-primary",
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