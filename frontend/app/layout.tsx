import type { Metadata } from "next";
import "./globals.css";

// Page metadata used by Next.js for the document title and description
export const metadata: Metadata = {
  title: "Mystery Engine",
  description: "AI-powered interactive mystery",
};

// Root layout wrapping all pages with the global CSS and HTML shell
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
