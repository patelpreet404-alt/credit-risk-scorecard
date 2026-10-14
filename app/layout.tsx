import type { Metadata } from "next";
import "./globals.css";
import "./metrics.css";

export const metadata: Metadata = {
  title: "Ledgerline — Credit Risk Intelligence",
  description: "An interactive credit portfolio monitor and scorecard workbench.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
