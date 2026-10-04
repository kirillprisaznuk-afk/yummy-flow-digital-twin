import type { Metadata } from "next";
import { Shell } from "@/components/shell";
import { WorkspaceProvider } from "@/features/scenarios/workspace";
import "./globals.css";
export const metadata: Metadata = {
  title: "Yummy Flow · Operations intelligence",
  description:
    "Synthetic quick-commerce operations and unit economics decision support.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <WorkspaceProvider>
          <Shell>{children}</Shell>
        </WorkspaceProvider>
      </body>
    </html>
  );
}
