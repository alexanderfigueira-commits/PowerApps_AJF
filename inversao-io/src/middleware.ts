export { default } from "next-auth/middleware";

// Rotas que exigem autenticacao. Utilizadores nao autenticados sao
// redirecionados para /entrar (definido em authOptions.pages.signIn).
export const config = {
  matcher: ["/dashboard/:path*", "/assessment/:path*", "/diagnostico/:path*", "/roadmap/:path*"],
};
