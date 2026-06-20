"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { signIn } from "next-auth/react";
import { Button, FormError, Input, Label } from "@/components/ui";

export default function RegistoPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [aGuardar, setAGuardar] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setAGuardar(true);

    try {
      const res = await fetch("/api/registo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        setErro(data.erro ?? "Não foi possível criar a conta.");
        setAGuardar(false);
        return;
      }

      // Autentica automaticamente apos o registo.
      const login = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (login?.error) {
        // Conta criada, mas o login falhou: encaminha para a pagina de entrada.
        router.push("/entrar");
        return;
      }

      // Apos registo, segue para o assessment.
      router.push("/assessment");
    } catch {
      setErro("Ocorreu um erro. Tente novamente.");
      setAGuardar(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <Link
          href="/"
          className="mb-8 block text-center text-lg font-semibold tracking-tight text-accent"
        >
          INVERSÃO.IO
        </Link>

        <div className="rounded-lg border border-border p-6 shadow-sm">
          <h1 className="text-xl font-semibold text-foreground">Criar conta</h1>
          <p className="mt-1 text-sm text-muted">
            Comece o diagnóstico do seu negócio.
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            {erro && <FormError>{erro}</FormError>}

            <div>
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
              <p className="mt-1 text-xs text-muted">Mínimo 8 caracteres.</p>
            </div>

            <Button type="submit" disabled={aGuardar} className="w-full">
              {aGuardar ? "A criar conta..." : "Criar conta"}
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-muted">
          Já tem conta?{" "}
          <Link href="/entrar" className="font-medium text-accent underline">
            Entrar
          </Link>
        </p>
      </div>
    </main>
  );
}
