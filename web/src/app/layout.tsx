import type { Metadata } from "next";
import "./globals.css";
import SplashScreen from "@/components/SplashScreen";

export const metadata: Metadata = {
  title: "Ecotrace - Yazılım Projeleri İçin Yüksek Hassasiyetli Karbon Ayak İzi Ölçümü",
  description: "Granüler karbon ayak izi ölçümü için hafif bir Python kütüphanesi. Yazılım projelerinizin enerji tüketimini ve karbon emisyonlarını sıfır konfigürasyon ile ölçün.",
  keywords: ["karbon ayak izi", "yeşil yazılım", "green computing", "carbon footprint", "python", "nextjs", "energy optimization"],
  authors: [{ name: "Ecotrace Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className="h-full antialiased dark"
    >
      <body className="min-h-full flex flex-col bg-[#050806] text-zinc-100 font-sans selection:bg-emerald-500/30 selection:text-emerald-300">
        <SplashScreen />
        {children}
      </body>
    </html>
  );
}
