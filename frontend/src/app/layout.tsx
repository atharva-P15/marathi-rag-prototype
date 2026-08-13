import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Providers from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'मराठी मीडिया RAG — Marathi Media RAG Chatbot',
  description:
    'Ask questions about Marathi video content and get grounded answers with timestamps and source citations.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="mr" className="dark">
      <head>
        {/* Noto Sans Devanagari for Marathi text rendering */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={`${inter.className} bg-surface-900 text-white antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
