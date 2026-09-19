import { CorpusList } from "@/components/CorpusList";

export default function Home() {
  return (
    <main>
      <h1>lexicon</h1>
      <p className="muted">Grounded document Q&amp;A — every answer is citation-backed or refused.</p>
      <CorpusList />
    </main>
  );
}
