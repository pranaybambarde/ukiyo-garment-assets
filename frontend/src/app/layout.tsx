import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from '@/lib/providers';
import { Header } from '@/components/common/Header';
import { Footer } from '@/components/common/Footer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Ukiyo - Functional Luxury Activewear',
  description: 'Premium activewear designed for the modern Indian woman. Functional luxury that adapts to your lifestyle.',
  keywords: 'activewear, luxury, women, India, functional, premium, yoga, fitness',
  authors: [{ name: 'Ukiyo' }],
  openGraph: {
    title: 'Ukiyo - Functional Luxury Activewear',
    description: 'Premium activewear designed for the modern Indian woman.',
    type: 'website',
    locale: 'en_IN',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Ukiyo - Functional Luxury Activewear',
    description: 'Premium activewear designed for the modern Indian woman.',
  },
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-1">
              {children}
            </main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}