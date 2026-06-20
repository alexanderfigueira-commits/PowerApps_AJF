import Link from "next/link";

// Landing page publica de INVERSAO.IO (passo 3).
// Tom serio, profissional, paleta sobria, sem emojis.

function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/90 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link
          href="/"
          className="text-lg font-semibold tracking-tight text-accent"
        >
          INVERSÃO.IO
        </Link>
        <Link
          href="/entrar"
          className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground transition hover:bg-zinc-50"
        >
          Entrar
        </Link>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="mx-auto max-w-5xl px-4 py-20 text-center sm:py-28">
      <h1 className="mx-auto max-w-3xl text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
        Diagnóstico de Transformação para o seu Negócio
      </h1>
      <p className="mx-auto mt-6 max-w-2xl text-balance text-lg text-muted">
        Muitas empresas trabalham para reduzir custos quando o verdadeiro
        problema é estrutural. Descubra onde o seu negócio está invertido e
        receba um plano concreto para passar de baixo valor para alto valor.
      </p>
      <div className="mt-10 flex justify-center">
        <Link
          href="/registo"
          className="rounded-md bg-accent px-6 py-3 text-base font-medium text-white transition hover:bg-accent/90"
        >
          Começar Diagnóstico
        </Link>
      </div>
    </section>
  );
}

function Problema() {
  return (
    <section className="border-t border-border bg-zinc-50">
      <div className="mx-auto max-w-5xl px-4 py-20">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Tentou tudo e continua preso
        </h2>
        <div className="mt-8 max-w-3xl space-y-4 text-muted">
          <p>
            Muitas PMEs em turismo, restauração e construção sentem que correm
            cada vez mais depressa para ficar no mesmo lugar. Cortaram custos,
            adotaram tecnologia, otimizaram processos. E mesmo assim as margens
            continuam apertadas e o futuro incerto.
          </p>
          <p>
            O problema raramente é falta de esforço ou de eficiência. É
            estrutural. O negócio está organizado em torno de produzir mais
            barato em vez de criar mais valor — uma lógica invertida que nenhuma
            otimização resolve.
          </p>
          <p className="font-medium text-foreground">
            Enquanto a estrutura estiver invertida, trabalhar mais só reforça o
            problema.
          </p>
        </div>
      </div>
    </section>
  );
}

function Solucao() {
  const passos = [
    {
      numero: "1",
      titulo: "Diagnostica",
      texto:
        "Responde a 12 perguntas sobre o seu negócio. Em poucos minutos, sem jargão.",
    },
    {
      numero: "2",
      titulo: "Conversa",
      texto:
        "Dialoga com um consultor de IA que identifica a inversão específica da sua empresa e explora caminhos de transformação.",
    },
    {
      numero: "3",
      titulo: "Gera plano",
      texto:
        "Recebe um roadmap de transformação de 18 meses, concreto e mensurável, pronto a descarregar em PDF.",
    },
  ];

  return (
    <section className="mx-auto max-w-5xl px-4 py-20">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
        Como funciona
      </h2>
      <div className="mt-10 grid gap-6 sm:grid-cols-3">
        {passos.map((passo) => (
          <div
            key={passo.numero}
            className="rounded-lg border border-border p-6"
          >
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-accent text-sm font-semibold text-white">
              {passo.numero}
            </span>
            <h3 className="mt-4 text-lg font-semibold text-foreground">
              {passo.titulo}
            </h3>
            <p className="mt-2 text-sm text-muted">{passo.texto}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Precos() {
  const planos = [
    {
      nome: "Básico",
      preco: "€29",
      destaque: false,
      beneficios: [
        "Assessment completo",
        "Até 3 conversas de diagnóstico por mês",
        "Geração de roadmap em PDF",
      ],
    },
    {
      nome: "Premium",
      preco: "€79",
      destaque: true,
      beneficios: [
        "Assessment completo",
        "Conversas de diagnóstico ilimitadas",
        "Geração de roadmap em PDF",
        "Prioridade no desenvolvimento de novas funcionalidades",
      ],
    },
  ];

  return (
    <section
      id="precos"
      className="border-t border-border bg-zinc-50"
    >
      <div className="mx-auto max-w-5xl px-4 py-20">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          Preços
        </h2>
        <p className="mt-3 text-muted">
          Sem permanência. Cancele quando quiser.
        </p>
        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {planos.map((plano) => (
            <div
              key={plano.nome}
              className={`rounded-lg border p-8 ${
                plano.destaque
                  ? "border-accent bg-white shadow-sm"
                  : "border-border bg-white"
              }`}
            >
              <h3 className="text-lg font-semibold text-foreground">
                {plano.nome}
              </h3>
              <p className="mt-4">
                <span className="text-4xl font-semibold text-foreground">
                  {plano.preco}
                </span>
                <span className="text-muted"> /mês</span>
              </p>
              <ul className="mt-6 space-y-3 text-sm text-foreground">
                {plano.beneficios.map((b) => (
                  <li key={b} className="flex gap-2">
                    <span className="text-accent" aria-hidden>
                      —
                    </span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>
              <Link
                href="/registo"
                className={`mt-8 block rounded-md px-4 py-2.5 text-center text-sm font-medium transition ${
                  plano.destaque
                    ? "bg-accent text-white hover:bg-accent/90"
                    : "border border-border text-foreground hover:bg-zinc-50"
                }`}
              >
                Começar Diagnóstico
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Faq() {
  const perguntas = [
    {
      pergunta: "Como é diferente de consultoria?",
      resposta:
        "A consultoria tradicional é cara, lenta e muitas vezes genérica. Aqui obtém um diagnóstico estrutural e um roadmap específico para o seu negócio em minutos, por uma fração do custo, e pode revisitá-lo sempre que quiser.",
    },
    {
      pergunta: "Preciso de conhecimentos técnicos?",
      resposta:
        "Não. Responde a perguntas em linguagem simples sobre o seu negócio e conversa em português normal. Toda a análise é feita por si.",
    },
    {
      pergunta: "E se não gostar?",
      resposta:
        "Não há permanência. Pode cancelar a subscrição a qualquer momento, diretamente a partir da sua conta.",
    },
  ];

  return (
    <section className="mx-auto max-w-3xl px-4 py-20">
      <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
        Perguntas frequentes
      </h2>
      <dl className="mt-10 space-y-8">
        {perguntas.map((item) => (
          <div key={item.pergunta}>
            <dt className="text-base font-semibold text-foreground">
              {item.pergunta}
            </dt>
            <dd className="mt-2 text-muted">{item.resposta}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 px-4 py-10 sm:flex-row">
        <span className="text-sm font-semibold tracking-tight text-accent">
          INVERSÃO.IO
        </span>
        <p className="text-sm text-muted">
          © {new Date().getFullYear()} INVERSÃO.IO. Todos os direitos
          reservados.
        </p>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Problema />
        <Solucao />
        <Precos />
        <Faq />
      </main>
      <Footer />
    </>
  );
}
