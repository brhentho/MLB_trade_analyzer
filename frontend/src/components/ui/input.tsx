/**
 * Enhanced Input Component System
 * Accessible form inputs with validation states and baseball-specific patterns
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { AlertCircle, CheckCircle, Search, DollarSign } from "lucide-react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: "default" | "filled" | "outline";
  state?: "default" | "error" | "success" | "warning";
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  error?: string;
  success?: string;
  help?: string;
  loading?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    type = "text",
    variant = "default",
    state = "default",
    icon,
    iconPosition = "left",
    error,
    success,
    help,
    loading = false,
    disabled,
    id,
    ...props 
  }, ref) => {
    
    // Generate unique ID if not provided
    const inputId = id || React.useId();
    const helpId = `${inputId}-help`;
    const errorId = `${inputId}-error`;
    const successId = `${inputId}-success`;

    const baseStyles = [
      "form-input",
      "transition-colors duration-200",
      icon && iconPosition === "left" && "pl-10",
      icon && iconPosition === "right" && "pr-10",
      loading && "opacity-60 cursor-wait",
    ];

    const variants = {
      default: "",
      filled: "bg-muted border-muted focus:bg-background",
      outline: "border-2 bg-transparent",
    };

    const states = {
      default: "",
      error: "border-destructive focus:ring-destructive",
      success: "border-green-500 focus:ring-green-500",
      warning: "border-yellow-500 focus:ring-yellow-500",
    };

    // Determine ARIA attributes
    const ariaDescribedBy = [
      error && errorId,
      success && successId,
      help && helpId,
    ].filter(Boolean).join(" ") || undefined;

    return (
      <div className="relative">
        {/* Left Icon */}
        {icon && iconPosition === "left" && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none">
            <div className="h-4 w-4" aria-hidden="true">
              {icon}
            </div>
          </div>
        )}

        <input
          ref={ref}
          id={inputId}
          type={type}
          className={cn(
            baseStyles,
            variants[variant],
            states[state],
            className
          )}
          disabled={loading || disabled}
          aria-invalid={state === "error" ? "true" : undefined}
          aria-describedby={ariaDescribedBy}
          {...props}
        />

        {/* Right Icon */}
        {icon && iconPosition === "right" && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none">
            <div className="h-4 w-4" aria-hidden="true">
              {icon}
            </div>
          </div>
        )}

        {/* State Icons */}
        {!icon && state === "error" && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-destructive pointer-events-none">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
          </div>
        )}

        {!icon && state === "success" && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-green-500 pointer-events-none">
            <CheckCircle className="h-4 w-4" aria-hidden="true" />
          </div>
        )}

        {/* Loading indicator */}
        {loading && !icon && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 pointer-events-none">
            <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Help Text */}
        {help && !error && !success && (
          <p id={helpId} className="form-help mt-1">
            {help}
          </p>
        )}

        {/* Error Message */}
        {error && (
          <p id={errorId} className="form-error mt-1" role="alert">
            {error}
          </p>
        )}

        {/* Success Message */}
        {success && (
          <p id={successId} className="mt-1 text-sm text-green-600">
            {success}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

// Specialized input components

interface SearchInputProps extends Omit<InputProps, 'icon' | 'type'> {
  onSearch?: (value: string) => void;
  clearable?: boolean;
  placeholder?: string;
}

const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ 
    onSearch,
    clearable = true,
    placeholder = "Search...",
    onChange,
    value,
    className,
    ...props 
  }, ref) => {
    const [searchValue, setSearchValue] = React.useState(value || "");

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setSearchValue(newValue);
      onChange?.(e);
      onSearch?.(newValue);
    };

    const handleClear = () => {
      setSearchValue("");
      onSearch?.("");
      // Create a synthetic event for consistency
      if (onChange) {
        const event = {
          target: { value: "" },
        } as React.ChangeEvent<HTMLInputElement>;
        onChange(event);
      }
    };

    return (
      <div className="relative">
        <Input
          ref={ref}
          type="search"
          icon={<Search />}
          iconPosition="left"
          value={searchValue}
          onChange={handleChange}
          placeholder={placeholder}
          className={cn("pr-10", className)}
          {...props}
        />
        
        {clearable && searchValue && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Clear search"
          >
            <span className="sr-only">Clear search</span>
            ×
          </button>
        )}
      </div>
    );
  }
);
SearchInput.displayName = "SearchInput";

interface CurrencyInputProps extends Omit<InputProps, 'icon' | 'type'> {
  currency?: string;
  prefix?: string;
  suffix?: string;
}

const CurrencyInput = React.forwardRef<HTMLInputElement, CurrencyInputProps>(
  ({ 
    currency = "USD",
    prefix = "$",
    suffix = "M",
    placeholder = "0",
    className,
    ...props 
  }, ref) => {
    return (
      <div className="relative">
        <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground pointer-events-none">
          <DollarSign className="h-4 w-4" aria-hidden="true" />
        </div>
        
        <Input
          ref={ref}
          type="number"
          step="0.1"
          min="0"
          placeholder={placeholder}
          className={cn("pl-10 pr-8", className)}
          aria-label={`Amount in ${currency}`}
          {...props}
        />
        
        {suffix && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm text-muted-foreground pointer-events-none">
            {suffix}
          </div>
        )}
      </div>
    );
  }
);
CurrencyInput.displayName = "CurrencyInput";

// Field wrapper with label and validation
interface FieldProps {
  label: string;
  required?: boolean;
  error?: string;
  success?: string;
  help?: string;
  children: React.ReactNode;
  className?: string;
}

const Field: React.FC<FieldProps> = ({
  label,
  required = false,
  error,
  success,
  help,
  children,
  className,
}) => {
  const fieldId = React.useId();

  return (
    <div className={cn("form-field", className)}>
      <label 
        htmlFor={fieldId}
        className="form-label"
      >
        {label}
        {required && (
          <span className="text-destructive ml-1" aria-label="required">
            *
          </span>
        )}
      </label>
      
      {React.cloneElement(children as React.ReactElement, {
        id: fieldId,
        error,
        success,
        help,
      })}
    </div>
  );
};

export {
  Input,
  SearchInput,
  CurrencyInput,
  Field,
  type InputProps,
  type SearchInputProps,
  type CurrencyInputProps,
  type FieldProps,
};