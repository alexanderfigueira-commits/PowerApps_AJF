"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, FormError } from "@/components/ui";
import type { AssessmentQuestion } from "@/lib/assessment-questions";

export default function AssessmentFlow({
  questions,
}: {
  questions: AssessmentQuestion[];
}) {
  const router = useRouter();
  const [respostas, setRespostas] = useState<Record<number, string>>({});
  const [indice, setIndice] = useState(0);
  const [aRever, setARever] = useState(false);
  const [erro, setErro] = useState("");
  const [aGuardar, setAGuardar] = useState(false);

  const total = questions.length;
  const perguntaAtual = questions[indice];
  const respostaAtual = respostas[perguntaAtual.id] ?? "";

  function atualizar(id: number, valor: string) {
    setRespostas((prev) => ({ ...prev, [id]: valor }));
  }

  function avancar() {
    setErro("");
    if (respostaAtual.trim().length === 0) {
      setErro("Por favor responda antes de continuar.");
      return;
    }
    if (indice < total - 1) {
      setIndice(indice + 1);
    } else {
      setARever(true);
    }
  }

  function recuar() {
    setErro("");
    if (aRever) {
      setARever(false);
      return;
    }
    if (indice > 0) {
      setIndice(indice - 1);
    }
  }

  function editar(i: number) {
    setARever(false);
    setIndice(i);
  }

  async function submeter() {
    setErro("");

    const emFalta = questions.find(
      (q) => (respostas[q.id] ?? "").trim().length === 0,
    );
    if (emFalta) {
      setErro(`A pergunta ${emFalta.id} ainda não tem resposta.`);
      setARever(false);
      setIndice(questions.findIndex((q) => q.id === emFalta.id));
      return;
    }

    setAGuardar(true);
    try {
      const payload = {
        respostas: questions.map((q) => ({
          id: q.id,
          resposta: respostas[q.id].trim(),
        })),
      };

      const res = await fetch("/api/assessment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setErro(data.erro ?? "Não foi possível guardar as respostas.");
        setAGuardar(false);
        return;
      }

      router.push("/diagnostico");
    } catch {
      setErro("Ocorreu um erro. Tente novamente.");
      setAGuardar(false);
    }
  }

  // Ecra de revisao final.
  if (aRever) {
    return (
      <div className="mt-8">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Reveja as suas respostas
        </h2>
        <p className="mt-2 text-sm text-muted">
          Pode editar qualquer resposta antes de iniciar o diagnóstico.
        </p>

        <div className="mt-6 space-y-5">
          {questions.map((q) => (
            <div key={q.id} className="rounded-lg border border-border p-4">
              <div className="flex items-start justify-between gap-4">
                <p className="text-sm font-medium text-foreground">
                  {q.id}. {q.pergunta}
                </p>
                <button
                  type="button"
                  onClick={() => editar(questions.findIndex((x) => x.id === q.id))}
                  className="shrink-0 text-sm font-medium text-accent underline"
                >
                  Editar
                </button>
              </div>
              <p className="mt-2 whitespace-pre-wrap text-sm text-muted">
                {respostas[q.id]?.trim() || "(sem resposta)"}
              </p>
            </div>
          ))}
        </div>

        {erro && (
          <div className="mt-6">
            <FormError>{erro}</FormError>
          </div>
        )}

        <div className="mt-8 flex items-center justify-between">
          <Button variant="secondary" onClick={recuar} disabled={aGuardar}>
            Voltar
          </Button>
          <Button onClick={submeter} disabled={aGuardar}>
            {aGuardar ? "A guardar..." : "Iniciar diagnóstico"}
          </Button>
        </div>
      </div>
    );
  }

  // Ecra de uma pergunta.
  const progresso = Math.round(((indice + 1) / total) * 100);

  return (
    <div className="mt-8 flex flex-1 flex-col">
      <div>
        <div className="flex items-center justify-between text-sm text-muted">
          <span>
            Pergunta {indice + 1} de {total}
          </span>
          <span>{progresso}%</span>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-accent transition-all"
            style={{ width: `${progresso}%` }}
          />
        </div>
      </div>

      <div className="mt-10">
        <label
          htmlFor={`q-${perguntaAtual.id}`}
          className="block text-xl font-medium text-foreground"
        >
          {perguntaAtual.pergunta}
        </label>
        <textarea
          id={`q-${perguntaAtual.id}`}
          value={respostaAtual}
          onChange={(e) => atualizar(perguntaAtual.id, e.target.value)}
          rows={6}
          autoFocus
          className="mt-4 w-full resize-none rounded-md border border-border bg-white px-3 py-2 text-sm text-foreground outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
          placeholder="Escreva a sua resposta..."
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              avancar();
            }
          }}
        />
        <p className="mt-2 text-xs text-muted">
          Dica: pressione Cmd/Ctrl + Enter para avançar.
        </p>
      </div>

      {erro && (
        <div className="mt-4">
          <FormError>{erro}</FormError>
        </div>
      )}

      <div className="mt-8 flex items-center justify-between">
        <Button
          variant="secondary"
          onClick={recuar}
          disabled={indice === 0}
        >
          Anterior
        </Button>
        <Button onClick={avancar}>
          {indice < total - 1 ? "Seguinte" : "Rever respostas"}
        </Button>
      </div>
    </div>
  );
}
