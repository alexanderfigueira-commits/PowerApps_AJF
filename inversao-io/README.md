# INVERSÃO.IO

Plataforma SaaS que usa IA (Claude API) para diagnosticar onde uma PME está a
funcionar de forma "invertida" e gera um roadmap de transformação de 18 meses.

Stack: **Next.js 14 (App Router) + TypeScript + Tailwind CSS + PostgreSQL (Prisma)
+ NextAuth + Anthropic Claude API + Stripe**.

> Estado atual: **Passo 2 — Autenticação (registo e login).**
> Já feito: setup, modelo de dados, registo/login com NextAuth + bcrypt,
> proteção de rotas. A seguir: landing page, assessment, chat, roadmap,
> dashboard e pagamentos.

## Autenticação

- Registo em `/registo` (nome, email, password) — password com hash bcrypt
- Login em `/entrar` (NextAuth Credentials provider, sessão JWT)
- Rotas protegidas via `src/middleware.ts` (`/dashboard`, `/assessment`,
  `/diagnostico`, `/roadmap`) — redirecionam para `/entrar` se não autenticado
- Após registo, o utilizador é autenticado e encaminhado para o assessment

> Nota: não há recuperação de password neste MVP (intencional).

## Pré-requisitos

- Node.js 18+ (testado em Node 22)
- Uma base de dados PostgreSQL (local, ou na cloud via [Neon](https://neon.tech)
  ou [Railway](https://railway.app))

## Configuração

1. Instala as dependências:

   ```bash
   npm install
   ```

2. Copia o ficheiro de exemplo das variáveis de ambiente e preenche os valores:

   ```bash
   cp .env.example .env
   ```

   Variáveis necessárias:

   | Variável | Descrição |
   |---|---|
   | `DATABASE_URL` | String de ligação ao PostgreSQL |
   | `NEXTAUTH_SECRET` | Segredo do NextAuth (gera com `openssl rand -base64 32`) |
   | `NEXTAUTH_URL` | URL da app (`http://localhost:3000` em dev) |
   | `ANTHROPIC_API_KEY` | Chave da API Claude (apenas usada no servidor) |
   | `STRIPE_SECRET_KEY` | Chave secreta do Stripe |
   | `STRIPE_PUBLISHABLE_KEY` | Chave pública do Stripe |
   | `STRIPE_WEBHOOK_SECRET` | Segredo do webhook do Stripe |
   | `STRIPE_PRICE_BASIC` | Price ID do plano Básico (€29/mês) |
   | `STRIPE_PRICE_PREMIUM` | Price ID do plano Premium (€79/mês) |

3. Gera o cliente Prisma e aplica o schema à base de dados:

   ```bash
   npx prisma generate
   npx prisma migrate dev --name init
   ```

   > Em alternativa, para empurrar o schema sem criar uma migração:
   > `npx prisma db push`

## Correr localmente

```bash
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000).

## Scripts úteis

| Comando | O que faz |
|---|---|
| `npm run dev` | Servidor de desenvolvimento |
| `npm run build` | Build de produção |
| `npm run start` | Servir o build de produção |
| `npx prisma studio` | Interface visual para a base de dados |

## Modelo de dados

Definido em [`prisma/schema.prisma`](./prisma/schema.prisma):

- **User** — utilizadores (email + password com hash bcrypt)
- **Assessment** — respostas às 12 perguntas (JSON)
- **Conversation** — histórico de chat com a IA (JSON)
- **Roadmap** — roadmap gerado (markdown)
- **Subscription** — tier do utilizador (NONE / BASIC / PREMIUM) e dados Stripe
- **UsageLog** — registo de uso para limites por tier

## Deploy

- **Frontend/Backend**: [Vercel](https://vercel.com)
- **Base de dados**: [Neon](https://neon.tech) ou [Railway](https://railway.app)

Configura todas as variáveis de ambiente no painel da Vercel.
