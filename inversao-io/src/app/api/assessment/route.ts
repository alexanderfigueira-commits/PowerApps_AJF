import { NextResponse } from "next/server";
import type { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { getCurrentUserId } from "@/lib/session";
import {
  ASSESSMENT_QUESTIONS,
  type AssessmentAnswer,
} from "@/lib/assessment-questions";

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
    const respostas: unknown = body?.respostas;

    if (!Array.isArray(respostas) || respostas.length !== ASSESSMENT_QUESTIONS.length) {
      return NextResponse.json(
        { erro: "Respostas incompletas. Responda a todas as perguntas." },
        { status: 400 },
      );
    }

    // Normaliza e valida cada resposta contra a lista oficial de perguntas.
    const answers: AssessmentAnswer[] = [];
    for (const question of ASSESSMENT_QUESTIONS) {
      const item = (respostas as Array<{ id?: number; resposta?: unknown }>).find(
        (r) => r.id === question.id,
      );
      const resposta =
        typeof item?.resposta === "string" ? item.resposta.trim() : "";

      if (resposta.length === 0) {
        return NextResponse.json(
          { erro: `Responda à pergunta ${question.id}.` },
          { status: 400 },
        );
      }

      answers.push({
        id: question.id,
        pergunta: question.pergunta,
        resposta,
      });
    }

    const assessment = await prisma.assessment.create({
      data: {
        userId,
        answers: answers as unknown as Prisma.InputJsonValue,
      },
    });

    // Regista o uso para metricas/limites.
    await prisma.usageLog.create({
      data: { userId, action: "ASSESSMENT" },
    });

    return NextResponse.json(
      { ok: true, assessmentId: assessment.id },
      { status: 201 },
    );
  } catch (error) {
    console.error("Erro ao guardar assessment:", error);
    return NextResponse.json(
      { erro: "Não foi possível guardar as respostas. Tente novamente." },
      { status: 500 },
    );
  }
}
