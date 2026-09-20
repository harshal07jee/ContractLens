import type { ChatAnswer, ContractAnalysis, SourceChunk } from "./types";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, init);
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? "Something went wrong. Please try again.");
  }
  return response.json() as Promise<T>;
}

export function uploadContract(file: File) {
  const data = new FormData();
  data.append("file", file);
  return request<ContractAnalysis>("/api/contracts/upload", { method: "POST", body: data });
}

export function askContract(contractId: string, question: string) {
  return request<ChatAnswer>(`/api/contracts/${contractId}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
}

export function getSource(contractId: string, sourceId: string) {
  return request<SourceChunk>(`/api/contracts/${contractId}/source/${encodeURIComponent(sourceId)}`);
}
