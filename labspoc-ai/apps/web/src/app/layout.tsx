import "./globals.css";
export const metadata = { title: "LabSPOC AI | Virtual Lab Ambassador", description: "Evidence-aware virtual laboratory experience" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
