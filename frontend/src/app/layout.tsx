import { ThemeProvider } from "@/components/theme-provider"

export const metadata = {
  title: 'SellIA - Vende mientras duermes',
  description: 'Agentes de IA que automatizan todo tu proceso de ventas. Desde captar clientes hasta concretar la entrega.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="font-sans antialiased bg-background text-foreground">
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
