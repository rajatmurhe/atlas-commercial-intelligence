import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Atlas — Commercial Intelligence",
  description:
    "An evidence-first commercial analytics workbench. A synthetic pharmaceutical portfolio demonstration.",
};
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
