import {
  getAnthropic,
  CLAUDE_MODEL,
  SEED_USER_MESSAGE,
  type ChatMessage,
} from "@/lib/anthropic";
import { formatarRespostas, type AssessmentAnswer } from "@/lib/assessment-questions";

// ---------------------------------------------------------------------------
// Arquitetura de 3 passos: Analista -> Critico -> Resposta.
// A IA "pensa" em camadas escondidas antes de falar; o utilizador só vê a
// resposta final, destilada, mais os sinais do painel lateral.
// ---------------------------------------------------------------------------

export type InversaoTipo = "consciencia" | "estrutura" | "mercado";

// JSON interno produzido pelo Analista (o utilizador nunca o vê na íntegra).
export interface Diagnostico {
  inversao_dominante: InversaoTipo;
  nivel_valor: 1 | 2 | 3 | 4;
  causa_raiz: string;
  o_que_o_dono_nao_disse: string;
  crenca_limitante: string;
  ativo_subaproveitado: string;
  melhor_proxima_pergunta: string;
  porque_esta_pergunta: string;
  sinais_painel: string[];
  confianca: "alta" | "media" | "baixa";
}

// Dados que vão para o painel lateral (subconjunto seguro do diagnóstico).
export interface PainelData {
  inversaoDominante: InversaoTipo;
  nivelValor: number;
  sinais: string[];
  confianca: "alta" | "media" | "baixa";
}

export interface ResultadoPipeline {
  mensagem: string;
  diagnostico: Diagnostico;
  painel: PainelData;
}

// --- System prompts -------------------------------------------------------

const SYSTEM_ANALISTA = `És o motor de diagnóstico da INVERSÃO.IO. A tua função é analisar, não conversar. Ninguém vê o que produzes aqui, por isso sê implacavelmente honesto e específico.

O teu enquadramento é a deteção de inversão empresarial. Uma empresa está "invertida" quando procura resultados pela via contrária à que os geraria de verdade. Há três tipos de inversão, e tens de classificar qual domina:

1. INVERSÃO DE CONSCIÊNCIA — o dono não vê o problema real, ou tem uma crença que o prende. Ex: "o meu mercado só paga isto", quando não é verdade.
2. INVERSÃO DE ESTRUTURA — a forma como a empresa está montada (preços, custos, equipa, processos) reforça o baixo valor. Ex: paga-se por hora em vez de por valor entregue.
3. INVERSÃO DE MERCADO — a empresa compete num espaço comoditizado onde só o preço decide. Ex: vende "cama" num mar de camas.

Também posicionas a empresa num eixo de valor de 1 a 4:
1 — Baixo valor, competição por custo
2 — Volume com alguma margem
3 — Valor emergente, alguma diferenciação
4 — Alto valor, diferenciação clara

Recebes o assessment inicial e toda a conversa até agora. Analisa e devolve SÓ este JSON, sem texto à volta:

{
  "inversao_dominante": "consciencia | estrutura | mercado",
  "nivel_valor": 1,
  "causa_raiz": "a frase que descreve o problema verdadeiro, não o sintoma",
  "o_que_o_dono_nao_disse": "o que está implícito ou em falta nas respostas",
  "crenca_limitante": "a convicção que o prende, se houver",
  "ativo_subaproveitado": "o recurso que ele tem e não usa",
  "melhor_proxima_pergunta": "a UMA pergunta que mais faria avançar o diagnóstico",
  "porque_esta_pergunta": "porque é esta e não outra",
  "sinais_painel": ["3 sinais curtos para mostrar no painel lateral"],
  "confianca": "alta | media | baixa"
}

Regras:
- Nunca inventes. Se não tens dados, di-lo no campo confianca e foca a pergunta em obter o que falta.
- A causa raiz nunca é o sintoma. "Margem baixa" é sintoma. "Vende um produto indiferenciado num mercado de preço" é causa.
- A melhor pergunta nunca é genérica. "Quais são os seus objetivos?" é lixo. "O que é que o hóspede sente ao entrar que mais nenhum hotel da zona oferece?" abre o problema.
- nivel_valor é um inteiro entre 1 e 4. sinais_painel tem exatamente 3 itens curtos.`;

const SYSTEM_CRITICO = `És o revisor de qualidade da INVERSÃO.IO. Recebes a análise do diagnóstico e a pergunta que o analista escolheu fazer ao dono da empresa. A tua função é endurecer a qualidade.

Avalia a pergunta proposta contra estes critérios:
1. É específica a ESTA empresa, ou serviria para qualquer uma? (se serve para qualquer uma, falha)
2. Abre o problema, ou só recolhe informação morna?
3. Faria um dono parar e pensar "boa pergunta, nunca olhei assim"?
4. Evita jargão e soa a uma pessoa inteligente, não a um formulário?

Se a pergunta passa em tudo, devolve-a igual. Se falha, reescreve-a melhor.

Devolve SÓ este JSON:
{
  "pergunta_final": "a pergunta, melhorada se preciso",
  "mudou": false,
  "observacao_para_resposta": "tom ou ângulo que a resposta visível deve ter"
}`;

const SYSTEM_RESPOSTA = `És o consultor da INVERSÃO.IO em conversa com o dono de uma PME portuguesa. Falas em português europeu, claro e natural, como quem explica a um amigo inteligente. Sem jargão, sem traços, sem linguagem de comunicado.

Recebes uma análise interna do diagnóstico. NÃO a recites nem a expliques. Usa-a para falar com precisão.

A tua resposta tem de:
- Devolver ao dono a situação dele com mais clareza do que ele tinha. Nomeia o padrão exato.
- Ser honesta mesmo quando incomoda. Não suavizas a verdade, mas não és frio.
- Terminar com UMA pergunta, a que vem na análise. Uma só.
- Ser curta. Três a cinco frases. A inteligência está na precisão, não no comprimento.

Nunca digas "como IA". Nunca peças desculpa. Nunca faças listas. Fala como gente.

ANÁLISE INTERNA:
{diagnostico_json}

PERGUNTA A FAZER:
{pergunta_final}

OBSERVAÇÃO DE TOM:
{observacao}`;

// --- Helpers ---------------------------------------------------------------

function extrairTexto(resposta: { content: Array<{ type: string }> }): string {
  return (resposta.content as Array<{ type: string; text?: string }>)
    .filter((b) => b.type === "text")
    .map((b) => b.text ?? "")
    .join("")
    .trim();
}

// Extrai e faz parse do primeiro objeto JSON encontrado no texto.
function parseJson<T>(texto: string): T {
  const inicio = texto.indexOf("{");
  const fim = texto.lastIndexOf("}");
  if (inicio === -1 || fim === -1 || fim <= inicio) {
    throw new Error("Resposta sem JSON.");
  }
  return JSON.parse(texto.slice(inicio, fim + 1)) as T;
}

// Converte o histórico de mensagens em texto para os prompts.
export function historicoParaTexto(messages: ChatMessage[]): string {
  if (messages.length === 0) return "(ainda não há conversa)";
  return messages
    .map((m) => `${m.role === "user" ? "Dono" : "Consultor"}: ${m.content}`)
    .join("\n\n");
}

// --- Passo A: Analista -----------------------------------------------------

async function runAnalista(
  assessment: AssessmentAnswer[],
  historicoTexto: string,
): Promise<Diagnostico> {
  const anthropic = getAnthropic();
  const userContent = `ASSESSMENT:\n${formatarRespostas(
    assessment,
  )}\n\nCONVERSA ATÉ AGORA:\n${historicoTexto}`;

  const chamar = async () => {
    const r = await anthropic.messages.create({
      model: CLAUDE_MODEL,
      max_tokens: 800,
      temperature: 0.4,
      system: SYSTEM_ANALISTA,
      messages: [{ role: "user", content: userContent }],
    });
    return parseJson<Diagnostico>(extrairTexto(r));
  };

  // Trata erros de parsing com uma nova tentativa.
  try {
    return await chamar();
  } catch {
    return await chamar();
  }
}

// --- Passo B: Crítico ------------------------------------------------------

interface ResultadoCritico {
  pergunta_final: string;
  mudou: boolean;
  observacao_para_resposta: string;
}

async function runCritico(diagnostico: Diagnostico): Promise<ResultadoCritico> {
  const anthropic = getAnthropic();
  const pergunta = diagnostico.melhor_proxima_pergunta;
  const userContent = JSON.stringify({
    analise: diagnostico,
    pergunta_proposta: pergunta,
  });

  const chamar = async () => {
    const r = await anthropic.messages.create({
      model: CLAUDE_MODEL,
      max_tokens: 400,
      temperature: 0.4,
      system: SYSTEM_CRITICO,
      messages: [{ role: "user", content: userContent }],
    });
    return parseJson<ResultadoCritico>(extrairTexto(r));
  };

  try {
    return await chamar();
  } catch {
    // Fallback: mantém a pergunta do analista.
    return {
      pergunta_final: pergunta,
      mudou: false,
      observacao_para_resposta: "",
    };
  }
}

// --- Passo C: Resposta (o que o utilizador vê) -----------------------------

async function runResposta(
  diagnostico: Diagnostico,
  perguntaFinal: string,
  observacao: string,
  historicoTexto: string,
): Promise<string> {
  const anthropic = getAnthropic();
  const system = SYSTEM_RESPOSTA.replace(
    "{diagnostico_json}",
    JSON.stringify(diagnostico),
  )
    .replace("{pergunta_final}", perguntaFinal)
    .replace("{observacao}", observacao || "(sem observação adicional)");

  // Para a abertura (sem histórico) usamos a mensagem-semente.
  const userContent =
    historicoTexto && historicoTexto !== "(ainda não há conversa)"
      ? historicoTexto
      : SEED_USER_MESSAGE;

  const r = await anthropic.messages.create({
    model: CLAUDE_MODEL,
    max_tokens: 400,
    temperature: 0.7,
    system,
    messages: [{ role: "user", content: userContent }],
  });
  return extrairTexto(r);
}

// --- Pipeline completo -----------------------------------------------------

export function diagnosticoParaPainel(d: Diagnostico): PainelData {
  return {
    inversaoDominante: d.inversao_dominante,
    nivelValor: d.nivel_valor,
    sinais: Array.isArray(d.sinais_painel) ? d.sinais_painel.slice(0, 3) : [],
    confianca: d.confianca,
  };
}

export async function executarPipeline(opts: {
  assessment: AssessmentAnswer[];
  messages: ChatMessage[];
  comCritico?: boolean;
}): Promise<ResultadoPipeline> {
  const { assessment, messages, comCritico = true } = opts;
  const historicoTexto = historicoParaTexto(messages);

  // Passo A — análise profunda escondida.
  const diagnostico = await runAnalista(assessment, historicoTexto);

  // Passo B — auto-crítica da pergunta (opcional).
  let perguntaFinal = diagnostico.melhor_proxima_pergunta;
  let observacao = "";
  if (comCritico) {
    const critico = await runCritico(diagnostico);
    perguntaFinal = critico.pergunta_final || perguntaFinal;
    observacao = critico.observacao_para_resposta ?? "";
  }

  // Passo C — resposta humana e destilada.
  const mensagem = await runResposta(
    diagnostico,
    perguntaFinal,
    observacao,
    historicoTexto,
  );

  return { mensagem, diagnostico, painel: diagnosticoParaPainel(diagnostico) };
}
