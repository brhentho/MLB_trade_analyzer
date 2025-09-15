/**
 * Enhanced Navigation Component System
 * Responsive navigation with accessibility and baseball-themed design
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { 
  Menu, 
  X, 
  ChevronDown, 
  Home,
  Search,
  BarChart3,
  Users,
  Settings,
  Bell,
  User
} from "lucide-react";
import { Button } from "./button";
import { Badge } from "./badge";

interface NavigationItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ReactNode;
  badge?: string | number;
  active?: boolean;
  disabled?: boolean;
  children?: NavigationItem[];
  onClick?: () => void;
}

interface NavigationProps {
  items: NavigationItem[];
  currentPath?: string;
  logo?: React.ReactNode;
  actions?: React.ReactNode;
  variant?: "horizontal" | "vertical" | "mobile";
  className?: string;
  onItemClick?: (item: NavigationItem) => void;
}

// Main Navigation component
const Navigation: React.FC<NavigationProps> = ({
  items,
  currentPath,
  logo,
  actions,
  variant = "horizontal",
  className,
  onItemClick,
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);
  const [expandedItems, setExpandedItems] = React.useState<Set<string>>(new Set());

  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  // Toggle expanded item
  const toggleExpanded = (itemId: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(itemId)) {
      newExpanded.delete(itemId);
    } else {
      newExpanded.add(itemId);
    }
    setExpandedItems(newExpanded);
  };

  // Handle item click
  const handleItemClick = (item: NavigationItem) => {
    if (item.disabled) return;
    
    if (item.children && item.children.length > 0) {
      toggleExpanded(item.id);
    } else {
      onItemClick?.(item);
      setMobileMenuOpen(false);
    }
  };

  // Check if item is active
  const isActive = (item: NavigationItem) => {
    if (item.active !== undefined) return item.active;
    if (item.href && currentPath) return currentPath === item.href;
    return false;
  };

  // Render navigation item
  const renderNavItem = (item: NavigationItem, depth = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.has(item.id);
    const active = isActive(item);

    return (
      <div key={item.id} className="relative">
        <button
          onClick={() => handleItemClick(item)}
          disabled={item.disabled}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-md text-left transition-colors",
            "text-statslugger-text-secondary hover:bg-statslugger-navy-primary hover:text-statslugger-text-primary",
            "focus:bg-statslugger-navy-primary focus:text-statslugger-orange-primary focus:outline-none",
            "disabled:opacity-50 disabled:pointer-events-none",
            active && "bg-statslugger-orange-primary/20 text-statslugger-orange-primary font-medium border-r-2 border-statslugger-orange-primary",
            depth > 0 && "ml-6 text-sm",
            variant === "horizontal" && "w-auto px-4"
          )}
          aria-expanded={hasChildren ? isExpanded : undefined}
          aria-current={active ? "page" : undefined}
        >
          {/* Icon */}
          {item.icon && (
            <span className="shrink-0" aria-hidden="true">
              {item.icon}
            </span>
          )}

          {/* Label */}
          <span className="flex-1 truncate">{item.label}</span>

          {/* Badge */}
          {item.badge && (
            <Badge size="sm" variant="secondary">
              {item.badge}
            </Badge>
          )}

          {/* Expand indicator */}
          {hasChildren && (
            <ChevronDown 
              className={cn(
                "h-4 w-4 transition-transform duration-200",
                isExpanded && "rotate-180"
              )}
              aria-hidden="true"
            />
          )}
        </button>

        {/* Children */}
        {hasChildren && isExpanded && (
          <div className="mt-1 space-y-1">
            {item.children!.map(child => renderNavItem(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (variant === "mobile") {
    return (
      <>
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleMobileMenu}
          className="md:hidden"
          aria-label="Toggle navigation menu"
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>

        {/* Mobile menu overlay */}
        {mobileMenuOpen && (
          <>
            <div 
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm md:hidden"
              onClick={() => setMobileMenuOpen(false)}
              aria-hidden="true"
            />
            
            <div className="fixed inset-y-0 left-0 z-50 w-64 bg-statslugger-navy-deep border-r border-statslugger-navy-border md:hidden">
              <div className="flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-statslugger-navy-border">
                  {logo}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setMobileMenuOpen(false)}
                    aria-label="Close navigation menu"
                  >
                    <X className="h-5 w-5" />
                  </Button>
                </div>

                {/* Navigation items */}
                <nav className="flex-1 overflow-auto p-4" aria-label="Mobile navigation">
                  <div className="space-y-1">
                    {items.map(item => renderNavItem(item))}
                  </div>
                </nav>

                {/* Actions */}
                {actions && (
                  <div className="p-4 border-t border-statslugger-navy-border">
                    {actions}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </>
    );
  }

  if (variant === "vertical") {
    return (
      <nav 
        className={cn("space-y-1", className)}
        aria-label="Sidebar navigation"
      >
        {items.map(item => renderNavItem(item))}
      </nav>
    );
  }

  // Horizontal navigation (default)
  return (
    <nav 
      className={cn(
        "flex items-center gap-1",
        className
      )}
      aria-label="Main navigation"
    >
      {items.map(item => renderNavItem(item))}
    </nav>
  );
};

// Header component with navigation
interface HeaderProps {
  logo?: React.ReactNode;
  navigation?: NavigationItem[];
  actions?: React.ReactNode;
  sticky?: boolean;
  transparent?: boolean;
  className?: string;
}

const Header: React.FC<HeaderProps> = ({
  logo,
  navigation = [],
  actions,
  sticky = true,
  transparent = false,
  className,
}) => {
  return (
    <header
      className={cn(
        "border-b border-statslugger-navy-border",
        sticky && "sticky top-0 z-40",
        transparent ? "bg-statslugger-navy-primary/80 backdrop-blur supports-[backdrop-filter]:bg-statslugger-navy-primary/60" : "bg-statslugger-navy-primary",
        className
      )}
    >
      <div className="flex items-center justify-between p-4">
        {/* Logo */}
        <div className="flex items-center gap-4">
          {logo}
        </div>

        {/* Desktop Navigation */}
        <div className="hidden md:flex">
          <Navigation 
            items={navigation}
            variant="horizontal"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {actions}
          
          {/* Mobile menu */}
          <Navigation
            items={navigation}
            variant="mobile"
          />
        </div>
      </div>
    </header>
  );
};

// Sidebar component
interface SidebarProps {
  navigation: NavigationItem[];
  logo?: React.ReactNode;
  footer?: React.ReactNode;
  collapsed?: boolean;
  className?: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  navigation,
  logo,
  footer,
  collapsed = false,
  className,
}) => {
  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-statslugger-navy-deep border-r border-statslugger-navy-border",
        collapsed ? "w-16" : "w-64",
        "transition-all duration-300 ease-out",
        className
      )}
      aria-label="Sidebar navigation"
    >
      {/* Logo */}
      {logo && (
        <div className="p-4 border-b border-statslugger-navy-border">
          {logo}
        </div>
      )}

      {/* Navigation */}
      <div className="flex-1 overflow-auto p-4">
        <Navigation 
          items={navigation}
          variant="vertical"
        />
      </div>

      {/* Footer */}
      {footer && (
        <div className="p-4 border-t border-statslugger-navy-border">
          {footer}
        </div>
      )}
    </aside>
  );
};

// Breadcrumb component
interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({ items, className }) => {
  return (
    <nav aria-label="Breadcrumb" className={className}>
      <ol className="flex items-center gap-2 text-sm">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {index > 0 && (
              <span className="text-muted-foreground" aria-hidden="true">
                /
              </span>
            )}
            
            {item.current ? (
              <span 
                className="text-foreground font-medium"
                aria-current="page"
              >
                {item.label}
              </span>
            ) : (
              <a
                href={item.href}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                {item.label}
              </a>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};

// Default navigation items for Baseball Trade AI
export const defaultNavigation: NavigationItem[] = [
  {
    id: "home",
    label: "Dashboard",
    href: "/",
    icon: <Home className="h-4 w-4" />,
  },
  {
    id: "trade-finder",
    label: "Trade Finder",
    href: "/trade-finder",
    icon: <Search className="h-4 w-4" />,
  },
  {
    id: "analytics", 
    label: "Analytics",
    href: "/analytics",
    icon: <BarChart3 className="h-4 w-4" />,
    children: [
      {
        id: "team-analytics",
        label: "Team Analysis",
        href: "/analytics/teams",
      },
      {
        id: "player-analytics",
        label: "Player Stats",
        href: "/analytics/players",
      },
    ],
  },
  {
    id: "community",
    label: "Community",
    href: "/community",
    icon: <Users className="h-4 w-4" />,
    badge: "New",
  },
];

export {
  Navigation,
  Header,
  Sidebar,
  Breadcrumb,
  type NavigationProps,
  type NavigationItem,
  type HeaderProps,
  type SidebarProps,
  type BreadcrumbProps,
  type BreadcrumbItem,
};