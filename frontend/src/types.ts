export type ImageRecord = {
  id: number;
  filename: string;
  image_url: string;
  description: string | null;
  metadata: Record<string, unknown>;
  designer_tags: string[];
  designer_notes: string | null;
  designer: string | null;
  continent: string | null;
  country: string | null;
  city: string | null;
  captured_at: string | null;
  created_at: string;
  updated_at: string;
};

