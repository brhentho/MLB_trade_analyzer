import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: ["class"],
  theme: {
    extend: {
      // Baseball Trade AI Color System
      colors: {
        // Brand Colors
        brand: {
          primary: "#1e40af", // Blue 700 - Primary brand color
          secondary: "#dc2626", // Red 600 - Accent/alert color
          tertiary: "#059669", // Green 600 - Success/positive
        },
        
        // Semantic Colors
        baseball: {
          infield: "#22c55e", // Green 500 - Infield positions
          outfield: "#3b82f6", // Blue 500 - Outfield positions
          pitcher: "#f59e0b", // Amber 500 - Pitchers
          catcher: "#8b5cf6", // Violet 500 - Catchers
          dh: "#ef4444", // Red 500 - Designated Hitter
        },
        
        // Team Status Colors
        team: {
          "win-now": "#2563eb", // Blue 600 - Competitive teams
          retool: "#7c3aed", // Violet 600 - Rebuilding teams
          rebuild: "#ea580c", // Orange 600 - Full rebuild
        },
        
        // Performance Colors
        performance: {
          excellent: "#16a34a", // Green 600
          good: "#65a30d", // Lime 600
          average: "#ca8a04", // Yellow 600
          poor: "#dc2626", // Red 600
          terrible: "#991b1b", // Red 800
        },
        
        // Financial Colors
        financial: {
          luxury: "#dc2626", // Red 600 - Over luxury tax
          high: "#ea580c", // Orange 600 - High payroll
          medium: "#ca8a04", // Yellow 600 - Medium payroll
          low: "#16a34a", // Green 600 - Low payroll
          rookie: "#059669", // Emerald 600 - Rookie contracts
        },
        
        // Design System Colors
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      
      // Typography System
      fontFamily: {
        sans: ['var(--font-geist-sans)', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'Consolas', 'Monaco', 'monospace'],
        display: ['var(--font-geist-sans)', 'Inter', 'system-ui', 'sans-serif'],
      },
      
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        
        // Baseball-specific sizes
        'stat': ['2rem', { lineHeight: '2.25rem', fontWeight: '600' }],
        'jersey': ['1.5rem', { lineHeight: '2rem', fontWeight: '700' }],
        'score': ['3rem', { lineHeight: '1', fontWeight: '800' }],
      },
      
      // Spacing System
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
      
      // Border Radius System
      borderRadius: {
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
        'baseball': '0.375rem', // Standard baseball card radius
      },
      
      // Box Shadow System
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
        'modal': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
        'floating': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
      },
      
      // Animation System
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'spin-slow': 'spin 2s linear infinite',
        'bounce-subtle': 'bounceSubtle 2s infinite',
        'progress-bar': 'progressBar 2s ease-in-out infinite',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(100%)' },
          '100%': { transform: 'translateY(0%)' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(0%)' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-2px)' },
        },
        progressBar: {
          '0%': { transform: 'translateX(-100%)' },
          '50%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(100%)' },
        },
      },
      
      // Screen Size System
      screens: {
        'xs': '475px',
        '3xl': '1680px',
        '4xl': '1920px',
      },
      
      // Z-Index System
      zIndex: {
        'dropdown': '50',
        'modal': '100',
        'popover': '200',
        'tooltip': '300',
        'toast': '400',
        'overlay': '500',
      },
      
      // Grid System
      gridTemplateColumns: {
        'auto-fit': 'repeat(auto-fit, minmax(0, 1fr))',
        'auto-fill': 'repeat(auto-fill, minmax(0, 1fr))',
        'trade-cards': 'repeat(auto-fit, minmax(280px, 1fr))',
        'team-grid': 'repeat(auto-fit, minmax(300px, 1fr))',
        'player-grid': 'repeat(auto-fit, minmax(250px, 1fr))',
      },
      
      // Backdrop Blur
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/container-queries'),
    // Custom plugin for baseball-specific utilities
    function({ addUtilities, theme }: { addUtilities: any; theme: any }) {
      addUtilities({
        // Position-based utilities
        '.position-infield': {
          backgroundColor: theme('colors.baseball.infield'),
          color: 'white',
        },
        '.position-outfield': {
          backgroundColor: theme('colors.baseball.outfield'),
          color: 'white',
        },
        '.position-pitcher': {
          backgroundColor: theme('colors.baseball.pitcher'),
          color: 'white',
        },
        '.position-catcher': {
          backgroundColor: theme('colors.baseball.catcher'),
          color: 'white',
        },
        
        // Safe area utilities for mobile
        '.safe-top': {
          paddingTop: 'env(safe-area-inset-top)',
        },
        '.safe-bottom': {
          paddingBottom: 'env(safe-area-inset-bottom)',
        },
        '.safe-left': {
          paddingLeft: 'env(safe-area-inset-left)',
        },
        '.safe-right': {
          paddingRight: 'env(safe-area-inset-right)',
        },
        '.safe-x': {
          paddingLeft: 'env(safe-area-inset-left)',
          paddingRight: 'env(safe-area-inset-right)',
        },
        '.safe-y': {
          paddingTop: 'env(safe-area-inset-top)',
          paddingBottom: 'env(safe-area-inset-bottom)',
        },
        '.safe-all': {
          paddingTop: 'env(safe-area-inset-top)',
          paddingBottom: 'env(safe-area-inset-bottom)',
          paddingLeft: 'env(safe-area-inset-left)',
          paddingRight: 'env(safe-area-inset-right)',
        },
        
        // Focus visible utilities
        '.focus-ring': {
          '&:focus-visible': {
            outline: '2px solid rgb(59 130 246)',
            outlineOffset: '2px',
          },
        },
        
        // Text truncation utilities
        '.truncate-2': {
          display: '-webkit-box',
          '-webkit-line-clamp': '2',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },
        '.truncate-3': {
          display: '-webkit-box',
          '-webkit-line-clamp': '3',
          '-webkit-box-orient': 'vertical',
          overflow: 'hidden',
        },
        
        // Glass morphism effect
        '.glass': {
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(10px)',
          borderColor: 'rgba(255, 255, 255, 0.2)',
        },
        '.glass-dark': {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(10px)',
          borderColor: 'rgba(255, 255, 255, 0.1)',
        },
      });
    },
  ],
};

export default config;