import type { Metadata } from "next";
import "@fontsource/space-grotesk/600.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/jetbrains-mono/400.css";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";


export const metadata: Metadata = {
  title: "Social Trend Analyzer",
  description:
    "An NLP-Based Platform for Detecting Emerging Topics, Sentiment, and Trends from Social Media Text.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
