import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ouroboros Manifold",
  description:
    "A generational strategy game set in a living, stochastic world. One engine. Infinite eras.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" data-theme="auto" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=Sora:wght@300;400;500;600&display=swap"
          rel="stylesheet"
        />
        {/* Prevent flash of wrong theme */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var s=localStorage.getItem('om-theme');if(s&&s!=='auto')document.documentElement.setAttribute('data-theme',s)})();`,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
