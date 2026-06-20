import type { DefaultSession } from "next-auth";

// Estende os tipos do NextAuth para incluir o id do utilizador na sessao.
declare module "next-auth" {
  interface Session {
    user: {
      id: string;
    } & DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
  }
}
