import { redirect } from "next/navigation";
import Link from "next/link";
import { prisma } from "@/lib/prisma";
import { getCurrentUserId } from "@/lib/session";
import { verificarLimiteConversas } from "@/lib/usage";
import type { ChatMessage } from "@/lib/anthropic";
import ChatClient from "./ChatClient";

export default async function DiagnosticoPage() {
  const userId = await getCurrentUserId();
  if (!userId) {
    redirect("/entrar");
  }

  // É preciso ter respondido ao assessment para iniciar o diagnóstico.
  const assessment = await prisma.assessment.findFirst({
    where: { userId },
    orderBy: { createdAt: "desc" },
  });
  if (!assessment) {
    redirect("/assessment");
  }

  // Retoma a conversa mais recente, se existir.
  const conversation = await prisma.conversation.findFirst({
    where: { userId },
    orderBy: { updatedAt: "desc" },
  });

  const limite = await verificarLimiteConversas(userId);
  const messages = (conversation?.messages as unknown as ChatMessage[]) ?? [];

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <Link
            href="/dashboard"
            className="text-lg font-semibold tracking-tight text-accent"
          >
            INVERSÃO.IO
          </Link>
          <Link
            href="/dashboard"
            className="text-sm font-medium text-muted hover:text-foreground"
          >
            Dashboard
          </Link>
        </div>
      </header>

      <ChatClient
        conversationId={conversation?.id ?? null}
        initialMessages={messages}
        limite={limite}
      />
    </div>
  );
}
