import { NextResponse } from "next/server";
import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { getCurrentUserId } from "@/lib/session";
import { verificarLimiteConversas } from "@/lib/usage";
import {
  buildSystemPrompt,
  getAnthropic,
  CLAUDE_MODEL,
  SEED_USER_MESSAGE,
  type ChatMessage,
} from "@/lib/anthropic";
import type { AssessmentAnswer } from "@/lib/assessment-questions";

// Inicia uma nova conversa de diagnóstico: gera a primeira mensagem da IA a
// partir das respostas do assessment mais recente.
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

    // Verifica o limite de conversas do tier antes de iniciar.
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
    const system = buildSystemPrompt(answers);

    const anthropic = getAnthropic();
    const resposta = await anthropic.messages.create({
      model: CLAUDE_MODEL,
      max_tokens: 1500,
      system,
      messages: [{ role: "user", content: SEED_USER_MESSAGE }],
    });

    const texto = resposta.content
      .filter((b) => b.type === "text")
      .map((b) => (b.type === "text" ? b.text : ""))
      .join("")
      .trim();

    const messages: ChatMessage[] = [{ role: "assistant", content: texto }];

    // Cria a conversa e regista o uso (1 conversa = 1 sessão).
    const conversation = await prisma.conversation.create({
      data: {
        userId,
        messages: messages as unknown as Prisma.InputJsonValue,
      },
    });
    await prisma.usageLog.create({
      data: { userId, action: "CONVERSATION" },
    });

    return NextResponse.json(
      { conversationId: conversation.id, messages },
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
