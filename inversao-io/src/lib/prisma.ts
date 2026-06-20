import { PrismaClient } from "@prisma/client";

// Padrao recomendado para Next.js: reutiliza a mesma instancia em dev para
// evitar esgotar as ligacoes a base de dados com o hot-reload.
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["error", "warn"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
