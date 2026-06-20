"use client";

import type { PainelData, InversaoTipo } from "@/lib/diagnosis";

const ROTULO_INVERSAO: Record<InversaoTipo, string> = {
  consciencia: "Inversão de consciência",
  estrutura: "Inversão de estrutura",
  mercado: "Inversão de mercado",
};

const ROTULO_NIVEL: Record<number, string> = {
  1: "Baixo valor, competição por custo",
  2: "Volume com alguma margem",
  3: "Valor emergente, diferenciação",
  4: "Alto valor, diferenciação clara",
};

export default function Painel({
  painel,
  aAtualizar,
}: {
  painel: PainelData | null;
  aAtualizar: boolean;
}) {
  return (
    <aside className="rounded-lg border border-border bg-white p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">
          Leitura em tempo real
        </h2>
        {aAtualizar && (
          <span className="text-xs text-muted">a atualizar…</span>
        )}
      </div>

      {!painel ? (
        <p className="mt-4 text-sm text-muted">
          A análise do seu negócio aparece aqui à medida que conversa.
        </p>
      ) : (
        <div className="mt-4 space-y-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted">
              Tipo de inversão
            </p>
            <p className="mt-1 text-sm font-medium text-foreground">
              {ROTULO_INVERSAO[painel.inversaoDominante] ??
                painel.inversaoDominante}
            </p>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-muted">
              Nível de valor
            </p>
            <div className="mt-2 flex gap-1.5">
              {[1, 2, 3, 4].map((n) => (
                <div
                  key={n}
                  className={`h-2 flex-1 rounded-full ${
                    n <= painel.nivelValor ? "bg-accent" : "bg-border"
                  }`}
                />
              ))}
            </div>
            <p className="mt-1.5 text-xs text-muted">
              {painel.nivelValor}/4 — {ROTULO_NIVEL[painel.nivelValor] ?? ""}
            </p>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wide text-muted">
              Sinais detetados
            </p>
            <ul className="mt-2 space-y-1.5">
              {painel.sinais.map((s, i) => (
                <li key={i} className="flex gap-2 text-sm text-foreground">
                  <span className="text-accent" aria-hidden>
                    —
                  </span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="text-xs text-muted">Confiança: {painel.confianca}</p>
        </div>
      )}
    </aside>
  );
}
