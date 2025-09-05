/**
 * Enhanced Dialog/Modal Component System
 * Accessible modals with focus management and baseball-themed variants
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { Button } from "./button";

interface DialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}

interface DialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg" | "xl" | "full";
  showClose?: boolean;
  closeOnOverlayClick?: boolean;
  trapFocus?: boolean;
}

// Context for managing dialog state
const DialogContext = React.createContext<{
  open: boolean;
  onOpenChange: (open: boolean) => void;
} | null>(null);

// Hook to use dialog context
const useDialog = () => {
  const context = React.useContext(DialogContext);
  if (!context) {
    throw new Error("Dialog components must be used within a Dialog provider");
  }
  return context;
};

// Main Dialog component
const Dialog: React.FC<DialogProps> = ({ 
  open = false, 
  onOpenChange, 
  children 
}) => {
  const [internalOpen, setInternalOpen] = React.useState(open);
  
  const isOpen = onOpenChange !== undefined ? open : internalOpen;
  const setIsOpen = onOpenChange || setInternalOpen;

  // Prevent body scrolling when dialog is open
  React.useEffect(() => {
    if (isOpen) {
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isOpen]);

  // Handle escape key
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen, setIsOpen]);

  if (!isOpen) return null;

  return (
    <DialogContext.Provider value={{ open: isOpen, onOpenChange: setIsOpen }}>
      {children}
    </DialogContext.Provider>
  );
};

// Dialog overlay
const DialogOverlay = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "fixed inset-0 z-modal bg-black/50 backdrop-blur-sm",
        "animate-fade-in",
        className
      )}
      {...props}
    />
  )
);
DialogOverlay.displayName = "DialogOverlay";

// Dialog content
const DialogContent = React.forwardRef<HTMLDivElement, DialogContentProps>(
  ({ 
    className, 
    children, 
    size = "md",
    showClose = true,
    closeOnOverlayClick = true,
    trapFocus = true,
    ...props 
  }, ref) => {
    const { onOpenChange } = useDialog();
    const contentRef = React.useRef<HTMLDivElement>(null);
    const previousActiveElement = React.useRef<Element | null>(null);

    const sizes = {
      sm: "max-w-md",
      md: "max-w-lg", 
      lg: "max-w-2xl",
      xl: "max-w-4xl",
      full: "max-w-[95vw] max-h-[95vh]",
    };

    // Focus management
    React.useEffect(() => {
      if (trapFocus) {
        previousActiveElement.current = document.activeElement;
        
        // Focus the dialog content
        setTimeout(() => {
          const focusableElement = contentRef.current?.querySelector(
            'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
          ) as HTMLElement;
          
          if (focusableElement) {
            focusableElement.focus();
          } else {
            contentRef.current?.focus();
          }
        }, 100);

        // Return focus on unmount
        return () => {
          if (previousActiveElement.current instanceof HTMLElement) {
            previousActiveElement.current.focus();
          }
        };
      }
    }, [trapFocus]);

    // Focus trap
    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (!trapFocus) return;

      if (e.key === "Tab") {
        const focusableElements = contentRef.current?.querySelectorAll(
          'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (!focusableElements || focusableElements.length === 0) return;

        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    return (
      <>
        <DialogOverlay 
          onClick={closeOnOverlayClick ? () => onOpenChange(false) : undefined}
        />
        <div className="fixed inset-0 z-modal flex items-center justify-center p-4">
          <div
            ref={ref}
            className={cn(
              "relative bg-background border border-border rounded-lg shadow-xl",
              "animate-scale-in transition-all duration-200",
              "max-h-[90vh] overflow-hidden",
              sizes[size],
              className
            )}
            role="dialog"
            aria-modal="true"
            tabIndex={-1}
            onKeyDown={handleKeyDown}
            {...props}
          >
            <div ref={contentRef} className="focus:outline-none">
              {children}
            </div>
            
            {/* Close Button */}
            {showClose && (
              <Button
                variant="ghost"
                size="icon"
                className="absolute top-4 right-4 z-10"
                onClick={() => onOpenChange(false)}
                aria-label="Close dialog"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </>
    );
  }
);
DialogContent.displayName = "DialogContent";

// Dialog header
const DialogHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col space-y-2 p-6 pb-4",
        "border-b border-border",
        className
      )}
      {...props}
    />
  )
);
DialogHeader.displayName = "DialogHeader";

// Dialog title
const DialogTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, children, ...props }, ref) => (
    <h2
      ref={ref}
      className={cn(
        "text-xl font-semibold leading-none tracking-tight text-balance",
        className
      )}
      {...props}
    >
      {children}
    </h2>
  )
);
DialogTitle.displayName = "DialogTitle";

// Dialog description
const DialogDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("text-sm text-muted-foreground text-pretty", className)}
      {...props}
    >
      {children}
    </p>
  )
);
DialogDescription.displayName = "DialogDescription";

// Dialog body
const DialogBody = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("p-6 overflow-auto", className)}
      {...props}
    />
  )
);
DialogBody.displayName = "DialogBody";

// Dialog footer
const DialogFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col gap-2 p-6 pt-4",
        "border-t border-border",
        "sm:flex-row sm:justify-end",
        className
      )}
      {...props}
    />
  )
);
DialogFooter.displayName = "DialogFooter";

// Specialized dialogs

// Confirmation dialog
interface ConfirmDialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  variant?: "default" | "destructive";
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  onOpenChange,
  title,
  description,
  confirmText = "Confirm",
  cancelText = "Cancel", 
  variant = "default",
  onConfirm,
  onCancel,
  loading = false,
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleConfirm = async () => {
    try {
      setIsSubmitting(true);
      await onConfirm();
      onOpenChange?.(false);
    } catch (error) {
      console.error("Confirmation action failed:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    onCancel?.();
    onOpenChange?.(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent size="sm" closeOnOverlayClick={!isSubmitting}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            {cancelText}
          </Button>
          <Button 
            variant={variant === "destructive" ? "destructive" : "primary"}
            onClick={handleConfirm}
            loading={isSubmitting}
            loadingText="Processing..."
          >
            {confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// Trade details dialog
interface TradeDialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  trade?: {
    id: string;
    teams: string[];
    players: Array<{
      name: string;
      position: string;
      from: string;
      to: string;
    }>;
    analysis?: any;
  };
}

const TradeDialog: React.FC<TradeDialogProps> = ({
  open,
  onOpenChange,
  trade,
}) => {
  if (!trade) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent size="xl">
        <DialogHeader>
          <DialogTitle>Trade Analysis Details</DialogTitle>
          <DialogDescription>
            {trade.teams.join(" ↔ ")} Trade Proposal
          </DialogDescription>
        </DialogHeader>

        <DialogBody>
          <div className="space-y-6">
            {/* Player movements */}
            <div>
              <h3 className="font-medium mb-3">Player Movements</h3>
              <div className="space-y-2">
                {trade.players.map((player, index) => (
                  <div 
                    key={index}
                    className="flex items-center gap-4 p-3 border border-border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="font-medium">{player.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {player.position}
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {player.from} → {player.to}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Analysis results */}
            {trade.analysis && (
              <div>
                <h3 className="font-medium mb-3">AI Analysis</h3>
                <div className="p-4 bg-muted rounded-lg">
                  <pre className="text-sm whitespace-pre-wrap">
                    {JSON.stringify(trade.analysis, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </DialogBody>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange?.(false)}>
            Close
          </Button>
          <Button variant="primary">
            Share Trade
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter,
  DialogOverlay,
  ConfirmDialog,
  TradeDialog,
  useDialog,
  type DialogProps,
  type DialogContentProps,
  type ConfirmDialogProps,
  type TradeDialogProps,
};