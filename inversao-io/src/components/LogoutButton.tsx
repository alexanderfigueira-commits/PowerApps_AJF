"use client";

import { signOut } from "next-auth/react";
import { Button } from "@/components/ui";

export default function LogoutButton() {
  return (
    <Button variant="secondary" onClick={() => signOut({ callbackUrl: "/" })}>
      Terminar sessão
    </Button>
  );
}
