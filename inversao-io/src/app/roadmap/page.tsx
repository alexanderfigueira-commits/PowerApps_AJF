import { redirect } from "next/navigation";
import Link from "next/link";
import { getCurrentUserId } from "@/lib/session";

// Placeholder da geração de roadmap. Será construído no passo 6.
export default async function RoadmapPage() {
  const userId = await getCurrentUserId();
  if (!userId) {
    redirect("/entrar");
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-2xl font-semibold tracking-tight text-accent">
        INVERSÃO.IO
      </h1>
      <p className="mt-6 text-foreground">
        A geração e exportação do roadmap em PDF será construída num passo
        seguinte.
      </p>
      <Link
        href="/diagnostico"
        className="mt-4 inline-block text-sm font-medium text-accent underline"
      >
        Voltar ao diagnóstico
      </Link>
    </main>
  );
}
