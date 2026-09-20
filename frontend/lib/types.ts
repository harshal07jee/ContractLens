export type Evidence = { source_id?: string | null; chunk_id?: string | null; page: number; section?: string | null; excerpt: string };
export type CitedValue = { value: string; evidence: Evidence };
export type Overview = {
  parties: CitedValue[]; effective_date?: CitedValue | null; expiration_date?: CitedValue | null;
  renewal_terms: CitedValue[]; payment_terms: CitedValue[]; termination_terms: CitedValue[]; important_terms: CitedValue[];
};
export type Obligation = { party?: string | null; description: string; frequency?: string | null; deadline?: string | null; evidence: Evidence };
export type TimelineEvent = { title: string; date?: string | null; relative_deadline?: string | null; description: string; evidence: Evidence };
export type ContractAnalysis = { id: string; filename: string; page_count: number; status: "processing" | "processed" | "failed"; uploaded_at: string; overview: Overview; obligations: Obligation[]; timeline: TimelineEvent[] };
export type ChatAnswer = { answer: string; answer_status: "supported" | "insufficient_evidence"; citations: Evidence[] };
export type SourceChunk = Evidence & { contract_id: string; text: string };
