import { redirect } from "next/navigation";
import { getCurrentUserId } from "@/lib/session";
import { ASSESSMENT_QUESTIONS } from "@/lib/assessment-questions";
import AssessmentFlow from "./AssessmentFlow";

export default async function AssessmentPage() {
  const userId = await getCurrentUserId();
  if (!userId) {
    redirect("/entrar");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col px-4 py-10">
      <h1 className="text-lg font-semibold tracking-tight text-accent">
        INVERSÃO.IO
      </h1>
      <AssessmentFlow questions={ASSESSMENT_QUESTIONS} />
    </main>
  );
}
