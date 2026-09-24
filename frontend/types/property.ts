export interface PropertySearchResponse {
  id: number;
  external_id: string;

  title: string | null;
  description: string | null;

  neighborhood: string;
  usable_area: number;
  bedrooms: number;
  bathrooms: number;
  parking_spaces: number | null;

  price: number;

  similarity_score: number;
}