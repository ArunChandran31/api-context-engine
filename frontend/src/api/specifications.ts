import { apiRequest } from "./client";

export interface ApiSpecification {
  id: number;
  title: string;
  version: string | null;
  description: string | null;
  source_file: string;
  created_at: string;
}

export async function getSpecifications(): Promise<ApiSpecification[]> {
  return apiRequest<ApiSpecification[]>("/api/specifications");
}

export async function getSpecification(
  id: number,
): Promise<ApiSpecification> {
  return apiRequest<ApiSpecification>(`/api/specifications/${id}`);
}
