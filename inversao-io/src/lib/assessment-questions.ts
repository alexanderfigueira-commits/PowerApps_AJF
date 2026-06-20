// As 12 perguntas do assessment de INVERSAO.IO.
// Partilhadas entre o formulario (passo 4) e a construcao do contexto
// para a Claude API (passo 5).

export interface AssessmentQuestion {
  id: number;
  pergunta: string;
}

export const ASSESSMENT_QUESTIONS: AssessmentQuestion[] = [
  { id: 1, pergunta: "O que vende? (descreva o produto ou serviço principal)" },
  { id: 2, pergunta: "A quem vende? (quem é o seu cliente típico)" },
  { id: 3, pergunta: "Quanto custa produzir uma unidade do que vende?" },
  { id: 4, pergunta: "Quanto cobra por essa unidade?" },
  {
    id: 5,
    pergunta:
      "Qual é a sua margem real, depois de todos os custos fixos?",
  },
  {
    id: 6,
    pergunta:
      "Quanto do seu tempo passa a cortar custos versus a criar valor novo?",
  },
  { id: 7, pergunta: "Qual é o seu maior problema neste momento?" },
  {
    id: 8,
    pergunta:
      "Já tentou mudar alguma coisa no modelo de negócio? O quê e como correu?",
  },
  {
    id: 9,
    pergunta:
      "O que mais o assusta quando pensa em transformar o negócio?",
  },
  {
    id: 10,
    pergunta: "Como seria o sucesso para si daqui a 18 meses?",
  },
  {
    id: 11,
    pergunta:
      "Quanto poderia investir numa transformação, em dinheiro e em tempo?",
  },
  {
    id: 12,
    pergunta:
      "Qual é a sua maior convicção sobre por que as coisas não mudam?",
  },
];

// Estrutura de uma resposta guardada no modelo Assessment (answers: JSON).
export interface AssessmentAnswer {
  id: number;
  pergunta: string;
  resposta: string;
}

// Formata as respostas como texto para usar no system prompt da Claude API.
export function formatarRespostas(answers: AssessmentAnswer[]): string {
  return answers
    .map((a) => `${a.id}. ${a.pergunta}\nResposta: ${a.resposta}`)
    .join("\n\n");
}
