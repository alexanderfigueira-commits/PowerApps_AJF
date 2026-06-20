import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/prisma";
import { validarRegisto } from "@/lib/validation";

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => null);

    if (!body) {
      return NextResponse.json(
        { erro: "Pedido invalido." },
        { status: 400 },
      );
    }

    const validacao = validarRegisto(body);
    if (!validacao.ok) {
      return NextResponse.json({ erro: validacao.erro }, { status: 400 });
    }

    const name = (body.name as string).trim();
    const email = (body.email as string).toLowerCase().trim();
    const password = body.password as string;

    const existente = await prisma.user.findUnique({ where: { email } });
    if (existente) {
      return NextResponse.json(
        { erro: "Ja existe uma conta com este email." },
        { status: 409 },
      );
    }

    const passwordHash = await bcrypt.hash(password, 12);

    await prisma.user.create({
      data: {
        name,
        email,
        passwordHash,
        // Cria a subscricao com tier NONE por defeito.
        subscription: {
          create: { plan: "NONE" },
        },
      },
    });

    return NextResponse.json({ ok: true }, { status: 201 });
  } catch (error) {
    console.error("Erro no registo:", error);
    return NextResponse.json(
      { erro: "Ocorreu um erro ao criar a conta. Tente novamente." },
      { status: 500 },
    );
  }
}
