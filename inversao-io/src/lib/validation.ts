// Validacoes simples e partilhadas para o registo/login.

export function emailValido(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function validarRegisto(input: {
  name?: unknown;
  email?: unknown;
  password?: unknown;
}): { ok: true } | { ok: false; erro: string } {
  const { name, email, password } = input;

  if (typeof name !== "string" || name.trim().length < 2) {
    return { ok: false, erro: "Indique o seu nome." };
  }
  if (typeof email !== "string" || !emailValido(email)) {
    return { ok: false, erro: "Indique um email valido." };
  }
  if (typeof password !== "string" || password.length < 8) {
    return { ok: false, erro: "A password deve ter pelo menos 8 caracteres." };
  }

  return { ok: true };
}
