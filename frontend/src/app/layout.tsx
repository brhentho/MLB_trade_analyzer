import type { Metadata } from "next";
import { Barlow_Condensed, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const sans = Inter({ subsets: ["latin"], display: "swap", variable: "--font-sans" });
const display = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["600", "700"],
  display: "swap",
  variable: "--font-display",
});
const mono = JetBrains_Mono({ subsets: ["latin"], display: "swap", variable: "--font-mono" });

export const metadata: Metadata = {
  title: "StatSlugger: real-world front office",
  description: "Build MLB rosters with real players, stats and contracts. Find niche fits, grade trades.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sans.variable} ${display.variable} ${mono.variable}`}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
