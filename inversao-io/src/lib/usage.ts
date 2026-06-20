import { prisma } from "@/lib/prisma";

// Limite de conversas por mês no tier que não é Premium.
export const LIMITE_CONVERSAS_BASICO = 3;

function inicioDoMes(): Date {
  const agora = new Date();
  return new Date(agora.getFullYear(), agora.getMonth(), 1);
}

// Conta quantas conversas (sessões) o utilizador iniciou no mês atual.
export async function contarConversasNoMes(userId: string): Promise<number> {
  return prisma.usageLog.count({
    where: {
      userId,
      action: "CONVERSATION",
      createdAt: { gte: inicioDoMes() },
    },
  });
}

export interface EstadoLimite {
  plano: "NONE" | "BASIC" | "PREMIUM";
  ilimitado: boolean;
  usadas: number;
  limite: number | null;
  podeIniciar: boolean;
}

// Verifica se o utilizador pode iniciar uma nova conversa.
// PREMIUM é ilimitado; os restantes tiers têm limite mensal.
export async function verificarLimiteConversas(
  userId: string,
): Promise<EstadoLimite> {
  const subscription = await prisma.subscription.findUnique({
    where: { userId },
  });
  const plano = subscription?.plan ?? "NONE";

  if (plano === "PREMIUM") {
    return {
      plano,
      ilimitado: true,
      usadas: 0,
      limite: null,
      podeIniciar: true,
    };
  }

  const usadas = await contarConversasNoMes(userId);
  return {
    plano,
    ilimitado: false,
    usadas,
    limite: LIMITE_CONVERSAS_BASICO,
    podeIniciar: usadas < LIMITE_CONVERSAS_BASICO,
  };
}
