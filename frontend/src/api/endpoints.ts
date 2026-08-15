import { apiRequest } from "./client";

export interface ApiEndpointParameter {
  name: string;
  in: string;
  required?: boolean;
  schema?: Record<string, unknown>;
  description?: string | null;
}

export interface ApiEndpoint {
  id: number;
  api_specification_id: number;
  path: string;
  method: string;
  summary: string | null;
  description: string | null;
  operation_id: string | null;

  parameters: ApiEndpointParameter[] | null;
  request_body: Record<string, unknown> | null;
  responses: Record<string, Record<string, unknown>> | null;
  security: Array<Record<string, string[]>> | null;
}

export async function getEndpoints(
  specificationId: number,
): Promise<ApiEndpoint[]> {
  return apiRequest<ApiEndpoint[]>(
    `/api/endpoints/specification/${specificationId}`,
  );
}
