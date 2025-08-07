import type { Metadata } from "next";
import "./globals.css";
import Navigation from "@/components/layout/Navigation";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Trading Dashboard",
  description: "Real-time financial market dashboard",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <html lang="en">
      <body className="antialiased">
        <Navigation user={user} />
        {children}
      </body>
    </html>
  );
}
