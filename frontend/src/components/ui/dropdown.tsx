/**
 * Enhanced Dropdown/Select Component System
 * Accessible dropdown with keyboard navigation and baseball-specific features
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { Check, ChevronDown, Search, X } from "lucide-react";
import { Button } from "./button";
import { Input } from "./input";

interface DropdownOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
  group?: string;
  disabled?: boolean;
  metadata?: Record<string, any>;
}

interface DropdownProps {
  options: DropdownOption[];
  value?: string;
  placeholder?: string;
  searchable?: boolean;
  clearable?: boolean;
  disabled?: boolean;
  loading?: boolean;
  error?: string;
  onValueChange: (value: string) => void;
  onClear?: () => void;
  className?: string;
  dropdownClassName?: string;
  maxHeight?: number;
  renderOption?: (option: DropdownOption, isSelected: boolean) => React.ReactNode;
  emptyMessage?: string;
  groupBy?: boolean;
}

const Dropdown = React.forwardRef<HTMLButtonElement, DropdownProps>(
  ({
    options,
    value,
    placeholder = "Select an option...",
    searchable = false,
    clearable = false,
    disabled = false,
    loading = false,
    error,
    onValueChange,
    onClear,
    className,
    dropdownClassName,
    maxHeight = 320,
    renderOption,
    emptyMessage = "No options found",
    groupBy = false,
    ...props
  }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const [searchTerm, setSearchTerm] = React.useState("");
    const [focusedIndex, setFocusedIndex] = React.useState(-1);
    
    const dropdownRef = React.useRef<HTMLDivElement>(null);
    const searchInputRef = React.useRef<HTMLInputElement>(null);
    const optionsRefs = React.useRef<(HTMLButtonElement | null)[]>([]);

    // Filter options based on search term
    const filteredOptions = React.useMemo(() => {
      if (!searchTerm) return options;
      
      return options.filter(option =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        option.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        option.group?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }, [options, searchTerm]);

    // Group options if needed
    const groupedOptions = React.useMemo(() => {
      if (!groupBy) return { "": filteredOptions };
      
      return filteredOptions.reduce((groups, option) => {
        const group = option.group || "";
        if (!groups[group]) groups[group] = [];
        groups[group].push(option);
        return groups;
      }, {} as Record<string, DropdownOption[]>);
    }, [filteredOptions, groupBy]);

    // Find selected option
    const selectedOption = options.find(opt => opt.value === value);

    // Handle keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (disabled || loading) return;

      switch (e.key) {
        case "Enter":
        case "Space":
          if (!isOpen) {
            e.preventDefault();
            setIsOpen(true);
            if (searchable) {
              setTimeout(() => searchInputRef.current?.focus(), 50);
            }
          }
          break;
          
        case "Escape":
          if (isOpen) {
            e.preventDefault();
            setIsOpen(false);
            setSearchTerm("");
          }
          break;
          
        case "ArrowDown":
          e.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else {
            const nextIndex = Math.min(focusedIndex + 1, filteredOptions.length - 1);
            setFocusedIndex(nextIndex);
            optionsRefs.current[nextIndex]?.scrollIntoView({ block: "nearest" });
          }
          break;
          
        case "ArrowUp":
          e.preventDefault();
          if (isOpen) {
            const prevIndex = Math.max(focusedIndex - 1, 0);
            setFocusedIndex(prevIndex);
            optionsRefs.current[prevIndex]?.scrollIntoView({ block: "nearest" });
          }
          break;
      }
    };

    // Handle option selection
    const handleOptionSelect = (optionValue: string) => {
      onValueChange(optionValue);
      setIsOpen(false);
      setSearchTerm("");
      setFocusedIndex(-1);
    };

    // Handle clear
    const handleClear = (e: React.MouseEvent) => {
      e.stopPropagation();
      onClear?.();
      setSearchTerm("");
      setIsOpen(false);
    };

    // Close dropdown when clicking outside
    React.useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
          setIsOpen(false);
          setSearchTerm("");
        }
      };

      if (isOpen) {
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
      }
    }, [isOpen]);

    // Reset focused index when options change
    React.useEffect(() => {
      setFocusedIndex(-1);
    }, [filteredOptions]);

    return (
      <div className="relative" ref={dropdownRef}>
        {/* Trigger Button */}
        <Button
          ref={ref}
          variant="outline"
          className={cn(
            "w-full justify-between text-left font-normal",
            !selectedOption && "text-muted-foreground",
            error && "border-destructive",
            className
          )}
          onClick={() => !disabled && !loading && setIsOpen(!isOpen)}
          onKeyDown={handleKeyDown}
          disabled={disabled || loading}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-label="Select option"
          {...props}
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {selectedOption?.icon && (
              <span className="shrink-0" aria-hidden="true">
                {selectedOption.icon}
              </span>
            )}
            <span className="truncate">
              {selectedOption?.label || placeholder}
            </span>
          </div>
          
          <div className="flex items-center gap-1 shrink-0">
            {clearable && selectedOption && !disabled && !loading && (
              <button
                onClick={handleClear}
                className="p-0.5 hover:bg-muted rounded-sm transition-colors"
                aria-label="Clear selection"
                tabIndex={-1}
              >
                <X className="h-3 w-3" />
              </button>
            )}
            <ChevronDown 
              className={cn(
                "h-4 w-4 transition-transform duration-200",
                isOpen && "rotate-180"
              )}
              aria-hidden="true"
            />
          </div>
        </Button>

        {/* Dropdown Content */}
        {isOpen && (
          <div 
            className={cn(
              "absolute z-dropdown w-full mt-1 bg-popover border border-border rounded-md shadow-lg",
              dropdownClassName
            )}
            role="listbox"
            aria-label="Options"
          >
            {/* Search Input */}
            {searchable && (
              <div className="p-2 border-b border-border">
                <Input
                  ref={searchInputRef}
                  icon={<Search />}
                  placeholder="Search options..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="h-8"
                  autoFocus
                />
              </div>
            )}

            {/* Options List */}
            <div 
              className="overflow-auto py-1"
              style={{ maxHeight }}
            >
              {Object.entries(groupedOptions).map(([group, groupOptions]) => (
                <div key={group}>
                  {/* Group Header */}
                  {group && groupBy && (
                    <div className="px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider bg-muted/50">
                      {group}
                    </div>
                  )}
                  
                  {/* Group Options */}
                  {groupOptions.map((option, index) => {
                    const globalIndex = filteredOptions.indexOf(option);
                    const isSelected = option.value === value;
                    const isFocused = globalIndex === focusedIndex;
                    
                    return (
                      <button
                        key={option.value}
                        ref={(el) => (optionsRefs.current[globalIndex] = el)}
                        className={cn(
                          "w-full flex items-center justify-between px-3 py-2 text-left",
                          "hover:bg-muted focus:bg-muted focus:outline-none",
                          "transition-colors duration-150",
                          "disabled:opacity-50 disabled:pointer-events-none",
                          isSelected && "bg-primary/10 text-primary",
                          isFocused && "bg-muted"
                        )}
                        onClick={() => !option.disabled && handleOptionSelect(option.value)}
                        disabled={option.disabled}
                        role="option"
                        aria-selected={isSelected}
                        aria-disabled={option.disabled}
                        onMouseEnter={() => setFocusedIndex(globalIndex)}
                      >
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          {option.icon && (
                            <span className="shrink-0 text-muted-foreground">
                              {option.icon}
                            </span>
                          )}
                          <div className="min-w-0">
                            <div className="font-medium truncate">
                              {option.label}
                            </div>
                            {option.description && (
                              <div className="text-sm text-muted-foreground truncate">
                                {option.description}
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {renderOption ? (
                          renderOption(option, isSelected)
                        ) : isSelected ? (
                          <Check className="h-4 w-4 text-primary" aria-hidden="true" />
                        ) : null}
                      </button>
                    );
                  })}
                </div>
              ))}
              
              {/* Empty State */}
              {filteredOptions.length === 0 && (
                <div className="px-3 py-6 text-center text-muted-foreground">
                  <p className="text-sm">{emptyMessage}</p>
                  {searchTerm && (
                    <p className="text-xs mt-1">
                      No results for "{searchTerm}"
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <p className="mt-1 text-sm text-destructive" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Dropdown.displayName = "Dropdown";

// Team Dropdown - specialized for team selection
interface TeamDropdownProps extends Omit<DropdownProps, 'options' | 'renderOption'> {
  teams: Record<string, {
    name: string;
    city: string;
    division: string;
    colors?: { primary: string; secondary: string };
    budget_level?: string;
    competitive_window?: string;
  }>;
}

const TeamDropdown = React.forwardRef<HTMLButtonElement, TeamDropdownProps>(
  ({ teams, ...props }, ref) => {
    const options: DropdownOption[] = React.useMemo(() => {
      return Object.entries(teams).map(([key, team]) => ({
        value: key,
        label: team.name,
        description: `${team.city} • ${team.division}`,
        group: team.division,
        metadata: {
          colors: team.colors,
          budgetLevel: team.budget_level,
          competitiveWindow: team.competitive_window,
        },
      }));
    }, [teams]);

    const renderTeamOption = (option: DropdownOption, isSelected: boolean) => (
      <div className="flex items-center gap-2">
        {/* Team Color */}
        <div 
          className="w-3 h-3 rounded-full shrink-0"
          style={{ 
            backgroundColor: option.metadata?.colors?.primary || 'var(--primary)' 
          }}
          aria-hidden="true"
        />
        
        {/* Status Badges */}
        <div className="flex gap-1">
          {option.metadata?.budgetLevel && (
            <span className={cn(
              "px-1.5 py-0.5 text-xs font-medium rounded",
              option.metadata.budgetLevel === "high" && "bg-green-50 text-green-700",
              option.metadata.budgetLevel === "medium" && "bg-yellow-50 text-yellow-700",
              option.metadata.budgetLevel === "low" && "bg-red-50 text-red-700"
            )}>
              {option.metadata.budgetLevel.charAt(0).toUpperCase()}
            </span>
          )}
          
          {option.metadata?.competitiveWindow && (
            <span className={cn(
              "px-1.5 py-0.5 text-xs font-medium rounded",
              option.metadata.competitiveWindow === "win-now" && "bg-blue-50 text-blue-700",
              option.metadata.competitiveWindow === "retool" && "bg-purple-50 text-purple-700",
              option.metadata.competitiveWindow === "rebuild" && "bg-orange-50 text-orange-700"
            )}>
              {option.metadata.competitiveWindow === "win-now" ? "W" : 
               option.metadata.competitiveWindow === "retool" ? "R" : "B"}
            </span>
          )}
        </div>
        
        {isSelected && <Check className="h-4 w-4 ml-auto" />}
      </div>
    );

    return (
      <Dropdown
        ref={ref}
        options={options}
        renderOption={renderTeamOption}
        groupBy={true}
        searchable={true}
        clearable={true}
        {...props}
      />
    );
  }
);
TeamDropdown.displayName = "TeamDropdown";

// Multi-select dropdown
interface MultiSelectProps extends Omit<DropdownProps, 'value' | 'onValueChange'> {
  values: string[];
  onValuesChange: (values: string[]) => void;
  maxSelections?: number;
  showCount?: boolean;
}

const MultiSelect = React.forwardRef<HTMLButtonElement, MultiSelectProps>(
  ({
    options,
    values = [],
    onValuesChange,
    maxSelections,
    showCount = true,
    placeholder = "Select options...",
    className,
    ...props
  }, ref) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const [searchTerm, setSearchTerm] = React.useState("");

    const selectedOptions = options.filter(opt => values.includes(opt.value));
    const availableOptions = options.filter(opt => 
      (!maxSelections || values.length < maxSelections || values.includes(opt.value)) &&
      (opt.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
       opt.description?.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const handleToggleOption = (optionValue: string) => {
      const newValues = values.includes(optionValue)
        ? values.filter(v => v !== optionValue)
        : [...values, optionValue];
      onValuesChange(newValues);
    };

    const displayText = selectedOptions.length === 0 
      ? placeholder
      : selectedOptions.length === 1
      ? selectedOptions[0].label
      : `${selectedOptions.length} selected`;

    return (
      <div className="relative">
        <Button
          ref={ref}
          variant="outline"
          className={cn(
            "w-full justify-between text-left font-normal",
            selectedOptions.length === 0 && "text-muted-foreground",
            className
          )}
          onClick={() => setIsOpen(!isOpen)}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          {...props}
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="truncate">{displayText}</span>
            {showCount && selectedOptions.length > 1 && (
              <span className="shrink-0 bg-primary/10 text-primary px-1.5 py-0.5 rounded text-xs">
                {selectedOptions.length}
              </span>
            )}
          </div>
          <ChevronDown 
            className={cn(
              "h-4 w-4 transition-transform duration-200",
              isOpen && "rotate-180"
            )}
          />
        </Button>

        {isOpen && (
          <div className="absolute z-dropdown w-full mt-1 bg-popover border border-border rounded-md shadow-lg">
            {/* Search */}
            <div className="p-2 border-b border-border">
              <Input
                icon={<Search />}
                placeholder="Search options..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="h-8"
              />
            </div>

            {/* Selected Count */}
            {showCount && maxSelections && (
              <div className="px-3 py-2 text-xs text-muted-foreground border-b border-border">
                {values.length}/{maxSelections} selected
              </div>
            )}

            {/* Options */}
            <div className="max-h-60 overflow-auto py-1">
              {availableOptions.map((option) => {
                const isSelected = values.includes(option.value);
                
                return (
                  <button
                    key={option.value}
                    className={cn(
                      "w-full flex items-center gap-2 px-3 py-2 text-left",
                      "hover:bg-muted focus:bg-muted focus:outline-none",
                      "transition-colors duration-150",
                      option.disabled && "opacity-50 pointer-events-none"
                    )}
                    onClick={() => handleToggleOption(option.value)}
                    disabled={option.disabled}
                  >
                    <div 
                      className={cn(
                        "w-4 h-4 border-2 rounded flex items-center justify-center",
                        isSelected ? "bg-primary border-primary" : "border-border"
                      )}
                    >
                      {isSelected && <Check className="h-3 w-3 text-white" />}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{option.label}</div>
                      {option.description && (
                        <div className="text-sm text-muted-foreground truncate">
                          {option.description}
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
              
              {availableOptions.length === 0 && (
                <div className="px-3 py-6 text-center text-muted-foreground text-sm">
                  {searchTerm ? `No results for "${searchTerm}"` : "No options available"}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Overlay */}
        {isOpen && (
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
        )}
      </div>
    );
  }
);
MultiSelect.displayName = "MultiSelect";

export {
  Dropdown,
  TeamDropdown,
  MultiSelect,
  type DropdownProps,
  type DropdownOption,
  type TeamDropdownProps,
  type MultiSelectProps,
};