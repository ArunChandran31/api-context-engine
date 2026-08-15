import { apiRequest } from "./client";

export interface UploadResponse {
  specification_id: number;
  title: string;
  version: string;
  endpoints_created: number;
  filename: string;
}

export async function uploadSpecification(
  file: File,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<UploadResponse>("/api/upload", {
    method: "POST",
    body: formData,
  });
}
