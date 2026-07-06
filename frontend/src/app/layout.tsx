import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PronounceAI — English Pronunciation Scorer",
  description:
    "Upload your English speech audio and get instant pronunciation scoring with word-by-word feedback powered by AI. Free, private, and no account needed.",
  keywords: ["pronunciation", "English", "speech", "scoring", "AI", "audio"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0a0a12" />
      </head>
      <body>{children}</body>
    </html>
  );
}
