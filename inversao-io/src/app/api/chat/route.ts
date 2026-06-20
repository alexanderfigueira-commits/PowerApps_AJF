import { NextResponse } from "next/server";
import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { getCurrentUserId } from "@/lib/session";
import {
  buildSystemPrompt,
  getAnthropic,
  CLAUDE_MODEL,
  SEED_USER_MESSAGE,
  type ChatMessage,
} from "@/lib/anthropic";
import type { AssessmentAnswer } from "@/lib/assessment-questions";

// Continua uma conversa existente. Recebe { conversationId, mensagem } e
// devolve a resposta da IA em streaming (text/plain).
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
    const novoHistorico: ChatMessage[] = [
      ...historico,
      { role: "user", content: mensagem },
    ];

    const answers = assessment.answers as unknown as AssessmentAnswer[];
    const system = buildSystemPrompt(answers);
    const anthropic = getAnthropic();

    // Mensagens para a API: prepende o turno-semente (oculto) para manter a
    // alternância user/assistant correta a partir da abertura da IA.
    const apiMessages = [
      { role: "user" as const, content: SEED_USER_MESSAGE },
      ...novoHistorico.map((m) => ({ role: m.role, content: m.content })),
    ];

    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      async start(controller) {
        let completo = "";
        try {
          const claudeStream = anthropic.messages.stream({
            model: CLAUDE_MODEL,
            max_tokens: 1500,
            system,
            messages: apiMessages,
          });

          for await (const evento of claudeStream) {
            if (
              evento.type === "content_block_delta" &&
              evento.delta.type === "text_delta"
            ) {
              completo += evento.delta.text;
              controller.enqueue(encoder.encode(evento.delta.text));
            }
          }

          // Persiste a conversa completa (histórico + nova resposta).
          const messagesFinais: ChatMessage[] = [
            ...novoHistorico,
            { role: "assistant", content: completo.trim() },
          ];
          await prisma.conversation.update({
            where: { id: conversationId },
            data: {
              messages: messagesFinais as unknown as Prisma.InputJsonValue,
            },
          });
        } catch (error) {
          console.error("Erro no streaming do chat:", error);
          controller.enqueue(
            encoder.encode(
              "\n\n[Ocorreu um erro ao gerar a resposta. Tente novamente.]",
            ),
          );
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
      },
    });
  } catch (error) {
    console.error("Erro no chat:", error);
    return NextResponse.json(
      { erro: "Não foi possível processar a mensagem." },
      { status: 500 },
    );
  }
}
