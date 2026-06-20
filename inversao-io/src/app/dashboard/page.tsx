import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/session";
import LogoutButton from "@/components/LogoutButton";

// Placeholder do dashboard. Sera construido no passo 7.
export default async function DashboardPage() {
  const session = await getCurrentSession();
  if (!session) {
    redirect("/entrar");
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-accent">
          INVERSÃO.IO
        </h1>
        <LogoutButton />
      </div>
      <p className="mt-6 text-foreground">
        Olá, {session.user.name}. A sua conta foi criada com sucesso.
      </p>
      <p className="mt-2 text-sm text-muted">
        O dashboard completo será construído num passo seguinte.
      </p>
    </main>
  );
}
