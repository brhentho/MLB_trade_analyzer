/**
 * Enhanced Layout Component System
 * Responsive layouts with baseball-themed designs and accessibility
 */

import * as React from "react";
import { cn } from "@/lib/utils";

// Container component with responsive max-widths
interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
  centered?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

const Container = React.forwardRef<HTMLDivElement, ContainerProps>(
  ({ 
    className, 
    size = "2xl", 
    centered = true,
    padding = "md",
    children,
    ...props 
  }, ref) => {
    const sizes = {
      sm: "max-w-sm",
      md: "max-w-md", 
      lg: "max-w-lg",
      xl: "max-w-xl",
      "2xl": "max-w-7xl",
      full: "max-w-full",
    };

    const paddings = {
      none: "",
      sm: "px-4 py-2",
      md: "px-4 sm:px-6 lg:px-8 py-4",
      lg: "px-4 sm:px-6 lg:px-8 py-8",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "w-full",
          sizes[size],
          centered && "mx-auto",
          paddings[padding],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Container.displayName = "Container";

// Page header component
interface PageHeaderProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  breadcrumb?: React.ReactNode;
  sticky?: boolean;
}

const PageHeader = React.forwardRef<HTMLElement, PageHeaderProps>(
  ({ 
    className,
    title,
    description,
    actions,
    breadcrumb,
    sticky = false,
    ...props 
  }, ref) => {
    return (
      <header
        ref={ref}
        className={cn(
          "bg-background border-b border-border",
          sticky && "sticky top-0 z-40 backdrop-blur supports-[backdrop-filter]:bg-background/60",
          className
        )}
        {...props}
      >
        <Container>
          {breadcrumb && (
            <div className="mb-4">
              {breadcrumb}
            </div>
          )}
          
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-balance">
                {title}
              </h1>
              {description && (
                <p className="text-muted-foreground max-w-2xl text-pretty">
                  {description}
                </p>
              )}
            </div>
            
            {actions && (
              <div className="flex items-center gap-2 shrink-0">
                {actions}
              </div>
            )}
          </div>
        </Container>
      </header>
    );
  }
);
PageHeader.displayName = "PageHeader";

// Grid system with responsive breakpoints
interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: 1 | 2 | 3 | 4 | 5 | 6 | 12;
  gap?: "none" | "sm" | "md" | "lg" | "xl";
  responsive?: {
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

const Grid = React.forwardRef<HTMLDivElement, GridProps>(
  ({ 
    className, 
    cols = 1,
    gap = "md",
    responsive,
    children,
    ...props 
  }, ref) => {
    const gapClasses = {
      none: "gap-0",
      sm: "gap-2",
      md: "gap-4",
      lg: "gap-6",
      xl: "gap-8",
    };

    const baseGridClass = `grid-cols-${cols}`;
    const responsiveClasses = responsive ? Object.entries(responsive).map(
      ([breakpoint, cols]) => `${breakpoint}:grid-cols-${cols}`
    ).join(" ") : "";

    return (
      <div
        ref={ref}
        className={cn(
          "grid",
          baseGridClass,
          responsiveClasses,
          gapClasses[gap],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Grid.displayName = "Grid";

// Flexible layout component
interface FlexProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: "row" | "col";
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between" | "around" | "evenly";
  gap?: "none" | "sm" | "md" | "lg" | "xl";
  wrap?: boolean;
}

const Flex = React.forwardRef<HTMLDivElement, FlexProps>(
  ({ 
    className,
    direction = "row",
    align = "start",
    justify = "start",
    gap = "md",
    wrap = false,
    children,
    ...props 
  }, ref) => {
    const directionClasses = {
      row: "flex-row",
      col: "flex-col",
    };

    const alignClasses = {
      start: "items-start",
      center: "items-center", 
      end: "items-end",
      stretch: "items-stretch",
    };

    const justifyClasses = {
      start: "justify-start",
      center: "justify-center",
      end: "justify-end",
      between: "justify-between",
      around: "justify-around",
      evenly: "justify-evenly",
    };

    const gapClasses = {
      none: "gap-0",
      sm: "gap-2",
      md: "gap-4",
      lg: "gap-6",
      xl: "gap-8",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "flex",
          directionClasses[direction],
          alignClasses[align],
          justifyClasses[justify],
          gapClasses[gap],
          wrap && "flex-wrap",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Flex.displayName = "Flex";

// Stack component for consistent spacing
interface StackProps extends React.HTMLAttributes<HTMLDivElement> {
  spacing?: "none" | "xs" | "sm" | "md" | "lg" | "xl";
  align?: "start" | "center" | "end" | "stretch";
}

const Stack = React.forwardRef<HTMLDivElement, StackProps>(
  ({ 
    className,
    spacing = "md",
    align = "stretch",
    children,
    ...props 
  }, ref) => {
    const spacingClasses = {
      none: "space-y-0",
      xs: "space-y-1",
      sm: "space-y-2",
      md: "space-y-4",
      lg: "space-y-6",
      xl: "space-y-8",
    };

    const alignClasses = {
      start: "items-start",
      center: "items-center",
      end: "items-end", 
      stretch: "items-stretch",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "flex flex-col",
          spacingClasses[spacing],
          alignClasses[align],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Stack.displayName = "Stack";

// Baseball field layout (for visual trade representations)
interface BaseballLayoutProps extends React.HTMLAttributes<HTMLDivElement> {
  positions?: Record<string, React.ReactNode>;
  interactive?: boolean;
  showFieldLines?: boolean;
}

const BaseballLayout = React.forwardRef<HTMLDivElement, BaseballLayoutProps>(
  ({ 
    className,
    positions = {},
    interactive = false,
    showFieldLines = true,
    children,
    ...props 
  }, ref) => {
    const positionCoords = {
      // Infield positions (percentage based)
      C: { bottom: "5%", left: "50%", transform: "translateX(-50%)" },
      "1B": { bottom: "25%", right: "25%" },
      "2B": { bottom: "40%", right: "35%" },
      SS: { bottom: "40%", left: "35%" },
      "3B": { bottom: "25%", left: "25%" },
      
      // Outfield positions
      RF: { top: "20%", right: "15%" },
      CF: { top: "10%", left: "50%", transform: "translateX(-50%)" },
      LF: { top: "20%", left: "15%" },
      
      // Pitcher
      P: { bottom: "50%", left: "50%", transform: "translateX(-50%)" },
    };

    return (
      <div
        ref={ref}
        className={cn(
          "relative aspect-square rounded-lg overflow-hidden",
          showFieldLines && "baseball-green",
          interactive && "cursor-pointer",
          className
        )}
        {...props}
      >
        {/* Field background */}
        <div className="absolute inset-0">
          {/* Pitcher's mound */}
          <div 
            className="absolute w-4 h-4 rounded-full dirt-brown border border-brown-600"
            style={{
              bottom: "50%",
              left: "50%", 
              transform: "translate(-50%, 50%)"
            }}
          />
          
          {/* Home plate area */}
          <div 
            className="absolute w-6 h-6 diamond-shape dirt-brown border border-brown-600"
            style={{
              bottom: "5%",
              left: "50%",
              transform: "translateX(-50%)"
            }}
          />
          
          {showFieldLines && (
            <>
              {/* Baselines */}
              <div className="absolute bottom-0 left-1/2 w-px h-1/2 bg-white/30 transform -translate-x-1/2 rotate-45 origin-bottom" />
              <div className="absolute bottom-0 left-1/2 w-px h-1/2 bg-white/30 transform -translate-x-1/2 -rotate-45 origin-bottom" />
            </>
          )}
        </div>

        {/* Position markers */}
        {Object.entries(positions).map(([position, content]) => {
          const coords = positionCoords[position as keyof typeof positionCoords];
          if (!coords) return null;

          return (
            <div
              key={position}
              className="absolute"
              style={coords}
            >
              {content}
            </div>
          );
        })}

        {children}
      </div>
    );
  }
);
BaseballLayout.displayName = "BaseballLayout";

export {
  Container,
  PageHeader,
  Grid,
  Flex,
  Stack,
  BaseballLayout,
  type ContainerProps,
  type PageHeaderProps,
  type GridProps,
  type FlexProps,
  type StackProps,
  type BaseballLayoutProps,
};