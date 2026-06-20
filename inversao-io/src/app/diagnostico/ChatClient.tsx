"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, FormError } from "@/components/ui";
import type { ChatMessage } from "@/lib/anthropic";
import type { EstadoLimite } from "@/lib/usage";

export default function ChatClient({
  conversationId: conversationIdInicial,
  initialMessages,
  limite,
}: {
  conversationId: string | null;
  initialMessages: ChatMessage[];
  limite: EstadoLimite;
}) {
  const router = useRouter();
  const [conversationId, setConversationId] = useState(conversationIdInicial);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
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

  // Pelo menos uma troca: a IA abriu e o utilizador já respondeu pelo menos uma vez.
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

      if (!res.ok || !res.body) {
        const data = await res.json().catch(() => ({}));
        setErro(data.erro ?? "Não foi possível obter resposta.");
        setAResponder(false);
        return;
      }

      // Acrescenta uma mensagem de assistente vazia e preenche-a com o stream.
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setMessages((prev) => {
          const copia = [...prev];
          const ultima = copia[copia.length - 1];
          if (ultima && ultima.role === "assistant") {
            copia[copia.length - 1] = {
              ...ultima,
              content: ultima.content + chunk,
            };
          }
          return copia;
        });
      }
    } catch {
      setErro("Ocorreu um erro ao comunicar com a IA.");
    } finally {
      setAResponder(false);
    }
  }

  async function gerarRoadmap() {
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
            <Button
              className="mt-4"
              onClick={() => router.push("/dashboard")}
            >
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
              {aIniciar ? "A iniciar..." : "Iniciar diagnóstico"}
            </Button>
          </div>
        )}
      </main>
    );
  }

  // Conversa em curso.
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4">
      <div className="flex-1 space-y-5 py-6">
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
              {m.content || (
                <span className="text-muted">A escrever...</span>
              )}
            </div>
          </div>
        ))}
        {aResponder &&
          messages[messages.length - 1]?.role === "user" && (
            <div className="flex justify-start">
              <div className="rounded-lg border border-border bg-white px-4 py-3 text-sm text-muted">
                A escrever...
              </div>
            </div>
          )}
        <div ref={fimRef} />
      </div>

      <div className="sticky bottom-0 border-t border-border bg-background py-4">
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
          <Button type="submit" disabled={aResponder || input.trim().length === 0}>
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
    </main>
  );
}
