import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/components/Providers";

export const metadata: Metadata = {
  title: "INVERSÃO.IO — Diagnóstico de Transformação para o seu Negócio",
  description:
    "Diagnóstico com IA que identifica onde o seu negócio está invertido e gera um roadmap de transformação de 18 meses.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-PT">
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
