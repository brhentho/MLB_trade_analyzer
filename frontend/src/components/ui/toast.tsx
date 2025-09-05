/**
 * Enhanced Toast Notification System
 * Baseball-themed notifications with accessibility and custom styling
 */

import * as React from "react";
import { toast as hotToast, Toaster as HotToaster, Toast } from "react-hot-toast";
import { cn } from "@/lib/utils";
import { 
  CheckCircle, 
  AlertCircle, 
  Info, 
  X, 
  TrendingUp, 
  TrendingDown,
  Users,
  DollarSign,
  Clock
} from "lucide-react";

// Enhanced toast configuration
interface ToastOptions {
  duration?: number;
  position?: "top-left" | "top-center" | "top-right" | "bottom-left" | "bottom-center" | "bottom-right";
  style?: React.CSSProperties;
  className?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
  dismissible?: boolean;
}

// Custom toast component
const CustomToast: React.FC<{
  toast: Toast;
  variant: "success" | "error" | "warning" | "info" | "trade";
  title?: string;
  description: string;
  icon?: React.ReactNode;
  action?: ToastOptions['action'];
  dismissible?: boolean;
}> = ({ 
  toast: t, 
  variant, 
  title, 
  description, 
  icon, 
  action,
  dismissible = true 
}) => {
  const variants = {
    success: {
      bg: "bg-green-50 border-green-200",
      text: "text-green-800",
      icon: icon || <CheckCircle className="h-5 w-5 text-green-500" />,
    },
    error: {
      bg: "bg-red-50 border-red-200", 
      text: "text-red-800",
      icon: icon || <AlertCircle className="h-5 w-5 text-red-500" />,
    },
    warning: {
      bg: "bg-yellow-50 border-yellow-200",
      text: "text-yellow-800", 
      icon: icon || <AlertCircle className="h-5 w-5 text-yellow-500" />,
    },
    info: {
      bg: "bg-blue-50 border-blue-200",
      text: "text-blue-800",
      icon: icon || <Info className="h-5 w-5 text-blue-500" />,
    },
    trade: {
      bg: "bg-gradient-to-r from-green-50 to-blue-50 border-green-200",
      text: "text-gray-800",
      icon: icon || <TrendingUp className="h-5 w-5 text-green-500" />,
    },
  };

  const config = variants[variant];

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border shadow-lg backdrop-blur",
        "animate-slide-up transition-all duration-300",
        config.bg,
        t.visible ? "opacity-100 scale-100" : "opacity-0 scale-95"
      )}
      role="alert"
      aria-live="polite"
    >
      {/* Icon */}
      <div className="shrink-0 mt-0.5" aria-hidden="true">
        {config.icon}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {title && (
          <div className={cn("font-medium text-sm", config.text)}>
            {title}
          </div>
        )}
        <div className={cn(
          "text-sm", 
          config.text,
          title && "mt-1"
        )}>
          {description}
        </div>
        
        {action && (
          <button
            onClick={() => {
              action.onClick();
              hotToast.dismiss(t.id);
            }}
            className={cn(
              "mt-2 text-xs font-medium underline hover:no-underline transition-colors",
              config.text
            )}
          >
            {action.label}
          </button>
        )}
      </div>

      {/* Dismiss Button */}
      {dismissible && (
        <button
          onClick={() => hotToast.dismiss(t.id)}
          className={cn(
            "shrink-0 p-1 rounded-md hover:bg-black/5 transition-colors",
            "focus:outline-none focus:ring-2 focus:ring-current focus:ring-offset-1"
          )}
          aria-label="Dismiss notification"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

// Enhanced toast functions
export const toast = {
  success: (message: string, options?: ToastOptions & { title?: string }) => {
    return hotToast.custom((t) => (
      <CustomToast
        toast={t}
        variant="success"
        title={options?.title}
        description={message}
        icon={options?.icon}
        action={options?.action}
        dismissible={options?.dismissible}
      />
    ), {
      duration: options?.duration || 4000,
      position: options?.position || "top-right",
      ...options,
    });
  },

  error: (message: string, options?: ToastOptions & { title?: string }) => {
    return hotToast.custom((t) => (
      <CustomToast
        toast={t}
        variant="error"
        title={options?.title}
        description={message}
        icon={options?.icon}
        action={options?.action}
        dismissible={options?.dismissible}
      />
    ), {
      duration: options?.duration || 6000,
      position: options?.position || "top-right",
      ...options,
    });
  },

  warning: (message: string, options?: ToastOptions & { title?: string }) => {
    return hotToast.custom((t) => (
      <CustomToast
        toast={t}
        variant="warning"
        title={options?.title}
        description={message}
        icon={options?.icon}
        action={options?.action}
        dismissible={options?.dismissible}
      />
    ), {
      duration: options?.duration || 5000,
      position: options?.position || "top-right",
      ...options,
    });
  },

  info: (message: string, options?: ToastOptions & { title?: string }) => {
    return hotToast.custom((t) => (
      <CustomToast
        toast={t}
        variant="info"
        title={options?.title}
        description={message}
        icon={options?.icon}
        action={options?.action}
        dismissible={options?.dismissible}
      />
    ), {
      duration: options?.duration || 4000,
      position: options?.position || "top-right",
      ...options,
    });
  },

  // Baseball-specific toast variants
  tradeComplete: (message: string, options?: ToastOptions) => {
    return toast.success(message, {
      title: "Trade Analysis Complete!",
      icon: <TrendingUp className="h-5 w-5 text-green-500" />,
      ...options,
    });
  },

  tradeFailed: (message: string, options?: ToastOptions) => {
    return toast.error(message, {
      title: "Trade Analysis Failed",
      icon: <TrendingDown className="h-5 w-5 text-red-500" />,
      ...options,
    });
  },

  playerFound: (playerName: string, team: string, options?: ToastOptions) => {
    return toast.success(`Found ${playerName} from ${team}`, {
      title: "Player Match Found!",
      icon: <Users className="h-5 w-5 text-blue-500" />,
      ...options,
    });
  },

  salaryAlert: (message: string, options?: ToastOptions) => {
    return toast.warning(message, {
      title: "Salary Cap Alert",
      icon: <DollarSign className="h-5 w-5 text-yellow-500" />,
      ...options,
    });
  },

  analysisStarted: (estimatedTime?: number, options?: ToastOptions) => {
    const timeText = estimatedTime ? ` (Est. ${Math.ceil(estimatedTime / 60)} min)` : "";
    return toast.info(`AI analysis initiated${timeText}`, {
      title: "Analysis Started",
      icon: <Clock className="h-5 w-5 text-blue-500" />,
      ...options,
    });
  },

  // Batch operations
  promise: <T extends any>(
    promise: Promise<T>,
    {
      loading = "Loading...",
      success = "Success!",
      error = "Something went wrong",
    }: {
      loading?: string;
      success?: string | ((data: T) => string);
      error?: string | ((error: any) => string);
    }
  ) => {
    return hotToast.promise(promise, {
      loading: (t) => (
        <CustomToast
          toast={t}
          variant="info"
          description={loading}
          dismissible={false}
        />
      ),
      success: (data, t) => (
        <CustomToast
          toast={t}
          variant="success"
          description={typeof success === "function" ? success(data) : success}
        />
      ),
      error: (err, t) => (
        <CustomToast
          toast={t}
          variant="error"
          description={typeof error === "function" ? error(err) : error}
        />
      ),
    });
  },

  dismiss: (toastId?: string) => {
    hotToast.dismiss(toastId);
  },

  remove: (toastId: string) => {
    hotToast.remove(toastId);
  },
};

// Enhanced Toaster component with better defaults
interface ToasterProps {
  position?: "top-left" | "top-center" | "top-right" | "bottom-left" | "bottom-center" | "bottom-right";
  reverseOrder?: boolean;
  containerClassName?: string;
  toastOptions?: {
    className?: string;
    style?: React.CSSProperties;
    duration?: number;
  };
}

export const Toaster: React.FC<ToasterProps> = ({
  position = "top-right",
  reverseOrder = false,
  containerClassName,
  toastOptions,
}) => {
  return (
    <HotToaster
      position={position}
      reverseOrder={reverseOrder}
      containerClassName={cn(
        "fixed z-toast",
        // Safe area support for mobile devices
        position.includes("top") && "safe-top",
        position.includes("bottom") && "safe-bottom",
        containerClassName
      )}
      toastOptions={{
        duration: 4000,
        style: {
          borderRadius: "0.5rem",
          border: "1px solid hsl(var(--border))",
          fontSize: "0.875rem",
          maxWidth: "400px",
          ...toastOptions?.style,
        },
        className: cn(
          "backdrop-blur-sm",
          toastOptions?.className
        ),
        ...toastOptions,
      }}
    />
  );
};

export { CustomToast, type ToastOptions };