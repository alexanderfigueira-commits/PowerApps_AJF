import { NextResponse } from "next/server";
import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { getCurrentUserId } from "@/lib/session";
import type { ChatMessage } from "@/lib/anthropic";
import { executarPipeline } from "@/lib/diagnosis";
import type { AssessmentAnswer } from "@/lib/assessment-questions";

// Continua uma conversa. Corre o pipeline Analista -> Crítico -> Resposta e
// devolve dois objetos: a mensagem de texto e os dados do painel lateral.
export async function POST(request: Request) {
  try {
    const userId = await getCurrentUserId();
    if (!userId) {
      return NextResponse.json(
        { erro: "Sessão não encontrada. Faça login novamente." },
        { status: 401 },
      );
    }

    const body = await request.json().catch(() => null);
    const conversationId =
      typeof body?.conversationId === "string" ? body.conversationId : null;
    const mensagem =
      typeof body?.mensagem === "string" ? body.mensagem.trim() : "";

    if (!conversationId || mensagem.length === 0) {
      return NextResponse.json({ erro: "Pedido inválido." }, { status: 400 });
    }

    const conversation = await prisma.conversation.findUnique({
      where: { id: conversationId },
    });
    if (!conversation || conversation.userId !== userId) {
      return NextResponse.json(
        { erro: "Conversa não encontrada." },
        { status: 404 },
      );
    }

    const assessment = await prisma.assessment.findFirst({
      where: { userId },
      orderBy: { createdAt: "desc" },
    });
    if (!assessment) {
      return NextResponse.json(
        { erro: "Ainda não respondeu ao assessment." },
        { status: 400 },
      );
    }

    const historico = conversation.messages as unknown as ChatMessage[];
    const comNovaMensagem: ChatMessage[] = [
      ...historico,
      { role: "user", content: mensagem },
    ];
    const answers = assessment.answers as unknown as AssessmentAnswer[];

    // Corre os três passos com o histórico já incluindo a nova mensagem.
    const { mensagem: resposta, diagnostico, painel } = await executarPipeline({
      assessment: answers,
      messages: comNovaMensagem,
    });

    const messagesFinais: ChatMessage[] = [
      ...comNovaMensagem,
      { role: "assistant", content: resposta },
    ];

    await prisma.conversation.update({
      where: { id: conversationId },
      data: {
        messages: messagesFinais as unknown as Prisma.InputJsonValue,
        diagnostico: diagnostico as unknown as Prisma.InputJsonValue,
      },
    });

    return NextResponse.json({ mensagem: resposta, painel }, { status: 200 });
  } catch (error) {
    console.error("Erro no chat:", error);
    return NextResponse.json(
      { erro: "Não foi possível processar a mensagem." },
      { status: 500 },
    );
  }
}
