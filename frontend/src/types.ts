export type GarmentAttributes = {
  garment_type: string[];
  style: string[];
  material: string[];
  color_palette: string[];
  pattern: string[];
  season: string | null;
  occasion: string[];
  consumer_profile: string[];
  trend_notes: string[];
  location_context: {
    continent: string | null;
    country: string | null;
    city: string | null;
    scene: string | null;
  };
};

export type ImageRecord = {
  id: number;
  filename: string;
  image_url: string;
  description: string | null;
  metadata: GarmentAttributes;
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

export type FilterOptions = {
  garment_type: string[];
  style: string[];
  material: string[];
  color_palette: string[];
  pattern: string[];
  season: string[];
  occasion: string[];
  consumer_profile: string[];
  country: string[];
  city: string[];
  designer: string[];
};
