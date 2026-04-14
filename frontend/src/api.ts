import type { FilterOptions, ImageRecord } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function getImageUrl(path: string): string {
  return path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
}

export async function fetchImages(params = new URLSearchParams()): Promise<ImageRecord[]> {
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/api/images${query ? `?${query}` : ""}`);
  if (!response.ok) {
    throw new Error("Failed to load image library");
  }
  return response.json();
}

export async function fetchFilters(): Promise<FilterOptions> {
  const response = await fetch(`${API_BASE_URL}/api/filters`);
  if (!response.ok) {
    throw new Error("Failed to load filters");
  }
  return response.json();
}

export async function uploadImage(formData: FormData): Promise<ImageRecord> {
  const response = await fetch(`${API_BASE_URL}/api/images`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? "Failed to upload image");
  }
  return response.json();
}

export async function deleteImage(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/images/${id}`, {
    method: "DELETE"
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? "Failed to delete image");
  }
}
