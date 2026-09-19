import type { Metadata } from "next";

import { IdentityBar } from "@/components/IdentityBar";
import { IdentityProvider } from "@/lib/identity";

import "./globals.css";

export const metadata: Metadata = {
  title: "lexicon",
  description: "Grounded document Q&A — every answer is citation-backed or refused.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <IdentityProvider>
          <header className="site-header">
            <span className="site-header__brand">lexicon</span>
            <IdentityBar />
          </header>
          {children}
        </IdentityProvider>
      </body>
    </html>
  );
}
