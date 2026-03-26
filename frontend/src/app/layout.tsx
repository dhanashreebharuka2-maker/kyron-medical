import type { Metadata } from "next";
import type { ReactNode } from "react";
import { DM_Sans, Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-geist-sans" });
const dm = DM_Sans({ subsets: ["latin"], variable: "--font-display" });

export const metadata: Metadata = {
  title: "Kyron Medical — Patient Assistant",
  description: "Schedule visits, refill routing, and office information.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${dm.variable}`}>
      <body
        className="font-sans antialiased"
        style={{
          /* Fallback if Tailwind/global CSS fails to load (e.g. corrupt .next cache) */
          backgroundColor: "#f0f9ff",
          color: "#0f172a",
        }}
      >
        {children}
      </body>
    </html>
  );
}
