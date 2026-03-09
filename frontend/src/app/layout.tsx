import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tayste - AI A&R Intelligence",
  description: "AI-powered artist discovery and scouting platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-gray-200 antialiased">
        {children}
      </body>
    </html>
  );
}
