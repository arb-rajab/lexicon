import type { Metadata } from "next";

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
      <body>{children}</body>
    </html>
  );
}
