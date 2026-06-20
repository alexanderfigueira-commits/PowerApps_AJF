import { NextResponse } from "next/server";
import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { getCurrentUserId } from "@/lib/session";
import { verificarLimiteConversas } from "@/lib/usage";
import type { ChatMessage } from "@/lib/anthropic";
import { executarPipeline } from "@/lib/diagnosis";
import type { AssessmentAnswer } from "@/lib/assessment-questions";

// Inicia uma nova conversa: corre o pipeline (Analista -> Crítico -> Resposta)
// sem histórico para gerar a primeira observação da IA e o painel inicial.
export async function POST() {
  try {
    const userId = await getCurrentUserId();
    if (!userId) {
      return NextResponse.json(
        { erro: "Sessão não encontrada. Faça login novamente." },
        { status: 401 },
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

    const limite = await verificarLimiteConversas(userId);
    if (!limite.podeIniciar) {
      return NextResponse.json(
        {
          erro: `Atingiu o limite de ${limite.limite} conversas este mês no plano atual. Faça upgrade para Premium para conversas ilimitadas.`,
          limiteAtingido: true,
        },
        { status: 403 },
      );
    }

    const answers = assessment.answers as unknown as AssessmentAnswer[];
    const { mensagem, diagnostico, painel } = await executarPipeline({
      assessment: answers,
      messages: [],
    });

    const messages: ChatMessage[] = [{ role: "assistant", content: mensagem }];

    const conversation = await prisma.conversation.create({
      data: {
        userId,
        messages: messages as unknown as Prisma.InputJsonValue,
        diagnostico: diagnostico as unknown as Prisma.InputJsonValue,
      },
    });
    await prisma.usageLog.create({
      data: { userId, action: "CONVERSATION" },
    });

    return NextResponse.json(
      { conversationId: conversation.id, messages, painel },
      { status: 201 },
    );
  } catch (error) {
    console.error("Erro ao iniciar conversa:", error);
    return NextResponse.json(
      { erro: "Não foi possível iniciar o diagnóstico. Tente novamente." },
      { status: 500 },
    );
  }
}
