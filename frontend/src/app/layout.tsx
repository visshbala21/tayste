import type { Metadata } from "next";
import { Bebas_Neue } from "next/font/google";
import "./globals.css";

const bebasNeue = Bebas_Neue({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Tayste - AI A&R Intelligence",
  description: "AI-powered artist discovery and scouting platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={bebasNeue.variable}>
      <body className="min-h-screen bg-background text-[#f5f5f0] antialiased">
        {children}
      </body>
    </html>
  );
}
