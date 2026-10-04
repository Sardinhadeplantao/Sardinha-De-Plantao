import "./globals.css";
export const metadata = { title: "Kondratiev Monitor", description: "Monitor de ciclos econômicos de longa duração" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR"><body className="bg-slate-950 text-slate-100 antialiased">
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      <footer className="mx-auto max-w-6xl px-4 pb-10 text-xs text-slate-500">
        Leitura de contexto baseada em dados públicos. Não é recomendação de investimento. Evidência estatística sobre ciclos de Kondratiev é limitada.
      </footer>
    </body></html>
  );
}
