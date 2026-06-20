"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { signIn } from "next-auth/react";
import { Button, FormError, Input, Label } from "@/components/ui";

function EntrarForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState("");
  const [aEntrar, setAEntrar] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setAEntrar(true);

    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });

    if (res?.error) {
      setErro("Email ou password incorretos.");
      setAEntrar(false);
      return;
    }

    router.push(callbackUrl);
    router.refresh();
  }

  return (
    <div className="w-full max-w-sm">
      <Link
        href="/"
        className="mb-8 block text-center text-lg font-semibold tracking-tight text-accent"
      >
        INVERSÃO.IO
      </Link>

      <div className="rounded-lg border border-border p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-foreground">Entrar</h1>
        <p className="mt-1 text-sm text-muted">Aceda à sua conta.</p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          {erro && <FormError>{erro}</FormError>}

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
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <Button type="submit" disabled={aEntrar} className="w-full">
            {aEntrar ? "A entrar..." : "Entrar"}
          </Button>
        </form>
      </div>

      <p className="mt-6 text-center text-sm text-muted">
        Ainda não tem conta?{" "}
        <Link href="/registo" className="font-medium text-accent underline">
          Criar conta
        </Link>
      </p>
    </div>
  );
}

export default function EntrarPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <Suspense fallback={null}>
        <EntrarForm />
      </Suspense>
    </main>
  );
}
