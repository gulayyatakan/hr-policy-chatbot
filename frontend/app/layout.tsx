import React from "react";

export const metadata = {
  title: 'Chat Frontend',
  description: 'Minimal React/Next.js chat UI'
};

import '../globas.css'; // keep your file name as requested (root-level)

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
