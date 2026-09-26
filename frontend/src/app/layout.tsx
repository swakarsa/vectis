import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Vectis | Autonomous Release Safety & Semantic Blast-Radius Intelligence",
  description: "Autonomous pre-merge release safety engine powered by IBM Bob 2.0 & Granite 3.0",
  openGraph: {
    title: "VECTIS | Autonomous Release Safety Engine",
    description: "Semantic blast-radius intelligence & pre-merge release safety for enterprise monorepos.",
    images: [
      {
        url: "/vectis-hero-banner-16x9.png",
        width: 1920,
        height: 1080,
        alt: "VECTIS Master Banner",
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "VECTIS | Autonomous Release Safety Engine",
    description: "Semantic blast-radius intelligence & pre-merge release safety for enterprise monorepos.",
    images: ["/vectis-hero-banner-16x9.png"],
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/icon.png", type: "image/png", sizes: "32x32" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[#08090a] text-zinc-100 antialiased selection:bg-rose-500/20 selection:text-rose-200`}>
        {children}
      </body>
    </html>
  );
}
