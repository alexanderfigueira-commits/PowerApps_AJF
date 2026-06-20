"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, FormError } from "@/components/ui";
import type { ChatMessage } from "@/lib/anthropic";
import type { PainelData } from "@/lib/diagnosis";
import type { EstadoLimite } from "@/lib/usage";
import Painel from "./Painel";

export default function ChatClient({
  conversationId: conversationIdInicial,
  initialMessages,
  initialPainel,
  limite,
}: {
  conversationId: string | null;
  initialMessages: ChatMessage[];
  initialPainel: PainelData | null;
  limite: EstadoLimite;
}) {
  const router = useRouter();
  const [conversationId, setConversationId] = useState(conversationIdInicial);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [painel, setPainel] = useState<PainelData | null>(initialPainel);
  const [input, setInput] = useState("");
  const [aResponder, setAResponder] = useState(false);
  const [aIniciar, setAIniciar] = useState(false);
  const [erro, setErro] = useState("");
  const [limiteAtingido, setLimiteAtingido] = useState(
    !conversationIdInicial && !limite.podeIniciar,
  );

  const fimRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, aResponder]);

  const podeGerarRoadmap =
    messages.some((m) => m.role === "user") &&
    messages.some((m) => m.role === "assistant");

  async function iniciarConversa() {
    setErro("");
    setAIniciar(true);
    try {
      const res = await fetch("/api/chat/start", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (data.limiteAtingido) setLimiteAtingido(true);
        setErro(data.erro ?? "Não foi possível iniciar o diagnóstico.");
        setAIniciar(false);
        return;
      }
      setConversationId(data.conversationId);
      setMessages(data.messages);
      setPainel(data.painel ?? null);
    } catch {
      setErro("Ocorreu um erro. Tente novamente.");
    } finally {
      setAIniciar(false);
    }
  }

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    const texto = input.trim();
    if (!texto || !conversationId || aResponder) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: texto }]);
    setAResponder(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversationId, mensagem: texto }),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        setErro(data.erro ?? "Não foi possível obter resposta.");
        setAResponder(false);
        return;
      }

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.mensagem },
      ]);
      if (data.painel) setPainel(data.painel);
    } catch {
      setErro("Ocorreu um erro ao comunicar com a IA.");
    } finally {
      setAResponder(false);
    }
  }

  function gerarRoadmap() {
    if (!conversationId) return;
    router.push(`/roadmap?conversationId=${conversationId}`);
  }

  // Ecrã inicial: ainda não há conversa.
  if (!conversationId) {
    return (
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-12 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Diagnóstico
        </h1>
        <p className="mt-3 max-w-md text-muted">
          A IA vai analisar as suas respostas e iniciar uma conversa sobre a
          inversão que deteta no seu negócio.
        </p>

        {!limite.ilimitado && (
          <p className="mt-4 text-sm text-muted">
            Plano atual: usou {limite.usadas} de {limite.limite} conversas este
            mês.
          </p>
        )}

        {limiteAtingido ? (
          <div className="mt-6 max-w-md rounded-lg border border-border bg-zinc-50 p-6">
            <p className="text-sm text-foreground">
              Atingiu o limite de conversas deste mês. Faça upgrade para Premium
              para conversas ilimitadas.
            </p>
            <Button className="mt-4" onClick={() => router.push("/dashboard")}>
              Ver planos
            </Button>
          </div>
        ) : (
          <div className="mt-8">
            {erro && (
              <div className="mb-4">
                <FormError>{erro}</FormError>
              </div>
            )}
            <Button onClick={iniciarConversa} disabled={aIniciar}>
              {aIniciar ? "A analisar o seu negócio…" : "Iniciar diagnóstico"}
            </Button>
          </div>
        )}
      </main>
    );
  }

  // Conversa em curso: chat + painel lateral.
  return (
    <main className="mx-auto grid w-full max-w-5xl flex-1 gap-6 px-4 py-6 lg:grid-cols-[1fr_280px]">
      <div className="flex min-h-0 flex-col">
        <div className="flex-1 space-y-5">
          {messages.map((m, i) => (
            <div
              key={i}
              className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-4 py-3 text-sm ${
                  m.role === "user"
                    ? "bg-accent text-white"
                    : "border border-border bg-white text-foreground"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {aResponder && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-lg border border-border bg-white px-4 py-3 text-sm text-muted">
                <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
                A analisar…
              </div>
            </div>
          )}
          <div ref={fimRef} />
        </div>

        <div className="sticky bottom-0 mt-4 border-t border-border bg-background py-4">
          {erro && (
            <div className="mb-3">
              <FormError>{erro}</FormError>
            </div>
          )}
          <form onSubmit={enviar} className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={2}
              placeholder="Escreva a sua resposta..."
              className="flex-1 resize-none rounded-md border border-border bg-white px-3 py-2 text-sm text-foreground outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  enviar(e);
                }
              }}
              disabled={aResponder}
            />
            <Button
              type="submit"
              disabled={aResponder || input.trim().length === 0}
            >
              Enviar
            </Button>
          </form>
          <div className="mt-3 flex items-center justify-between">
            <p className="text-xs text-muted">
              Enter para enviar, Shift+Enter para nova linha.
            </p>
            <Button
              variant="secondary"
              onClick={gerarRoadmap}
              disabled={!podeGerarRoadmap || aResponder}
            >
              Gerar Roadmap
            </Button>
          </div>
        </div>
      </div>

      <div className="lg:sticky lg:top-6 lg:self-start">
        <Painel painel={painel} aAtualizar={aResponder} />
      </div>
    </main>
  );
}
