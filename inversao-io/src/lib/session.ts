import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

// Devolve a sessao do utilizador no servidor (ou null se nao autenticado).
export async function getCurrentSession() {
  return getServerSession(authOptions);
}

// Devolve o id do utilizador autenticado, ou null.
export async function getCurrentUserId(): Promise<string | null> {
  const session = await getCurrentSession();
  return session?.user?.id ?? null;
}
