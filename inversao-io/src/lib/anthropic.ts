import Anthropic from "@anthropic-ai/sdk";
import { formatarRespostas, type AssessmentAnswer } from "@/lib/assessment-questions";

// Modelo Claude usado em todo o produto (conforme especificacao).
export const CLAUDE_MODEL = "claude-sonnet-4-6";

let client: Anthropic | null = null;

// Cliente Anthropic (apenas no servidor). A chave nunca chega ao frontend.
export function getAnthropic(): Anthropic {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("ANTHROPIC_API_KEY não está configurada.");
  }
  if (!client) {
    client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
  }
  return client;
}

// System prompt do consultor de inversao empresarial, com as respostas do
// assessment injetadas como contexto.
export function buildSystemPrompt(answers: AssessmentAnswer[]): string {
  const respostas = formatarRespostas(answers);
  return `És um consultor de negócios sénior especializado em diagnóstico de inversão empresarial. A tua análise baseia-se na ideia de que muitas empresas funcionam de forma invertida: procuram lucro reduzindo custos em vez de criar valor, procuram tecnologia para fazer o mesmo mais barato em vez de fazer algo diferente, e têm estruturas que reforçam mentalidades de volume e baixo valor.

Recebeste as seguintes respostas de um assessment feito por um CEO de uma PME portuguesa:

${respostas}

A tua tarefa:
1. Identificar onde está a inversão específica desta empresa (é de consciência, de estrutura, ou de mercado?)
2. Fazer perguntas que revelem os problemas estruturais de raiz
3. Explorar caminhos concretos de transformação de baixo valor para alto valor
4. Ser direto e honesto, sem jargão corporativo

Fala em português europeu, de forma clara e natural, como se estivesses a explicar a um amigo inteligente. Não uses traços nem linguagem de comunicado. Sê empático mas não evites a verdade. Faz uma pergunta de cada vez.`;
}

// Mensagem inicial (oculta) que aciona a primeira observação da IA.
// Não é mostrada ao utilizador; serve apenas para a API ter um turno "user"
// antes da primeira resposta do assistente.
export const SEED_USER_MESSAGE =
  "Com base nas minhas respostas ao assessment, faz a tua primeira observação sobre a inversão que detetas no meu negócio e começa o diagnóstico.";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
