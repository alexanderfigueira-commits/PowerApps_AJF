import Link from "next/link";

// Placeholder da landing page. Sera construida no passo 3.
export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 px-4 text-center">
      <h1 className="text-3xl font-semibold tracking-tight text-accent">
        INVERSÃO.IO
      </h1>
      <p className="max-w-md text-muted">
        Diagnóstico de transformação para o seu negócio.
      </p>
      <div className="flex gap-3">
        <Link
          href="/registo"
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90"
        >
          Criar conta
        </Link>
        <Link
          href="/entrar"
          className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-zinc-50"
        >
          Entrar
        </Link>
      </div>
    </main>
  );
}
