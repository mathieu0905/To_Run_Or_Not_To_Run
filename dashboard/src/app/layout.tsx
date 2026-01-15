import "./globals.css";

export const metadata = { title: "SWE-bench Dashboard" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh">
      <body className="bg-gray-900 text-white min-h-screen">{children}</body>
    </html>
  );
}
