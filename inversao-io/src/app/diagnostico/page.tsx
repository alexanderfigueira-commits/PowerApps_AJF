import { redirect } from "next/navigation";
import Link from "next/link";
import { getCurrentUserId } from "@/lib/session";

// Placeholder do chat de diagnostico. Sera construido no passo 5.
export default async function DiagnosticoPage() {
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
        Respostas guardadas. O chat de diagnóstico com a IA será construído num
        passo seguinte.
      </p>
      <Link
        href="/dashboard"
        className="mt-4 inline-block text-sm font-medium text-accent underline"
      >
        Ir para o dashboard
      </Link>
    </main>
  );
}
