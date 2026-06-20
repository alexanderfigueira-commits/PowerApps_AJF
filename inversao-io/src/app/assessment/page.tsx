import { redirect } from "next/navigation";
import Link from "next/link";
import { getCurrentSession } from "@/lib/session";

// Placeholder do assessment. Sera construido no passo 4.
export default async function AssessmentPage() {
  const session = await getCurrentSession();
  if (!session) {
    redirect("/entrar");
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-2xl font-semibold tracking-tight text-accent">
        INVERSÃO.IO
      </h1>
      <p className="mt-6 text-foreground">
        Bem-vindo, {session.user.name}. O assessment de 12 perguntas será
        construído num passo seguinte.
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
