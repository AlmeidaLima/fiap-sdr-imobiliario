import type { PropertySearchResponse } from "../../types/property";

interface PropertyCardProps {
  property: PropertySearchResponse;
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(price);
}

function formatSimilarity(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export function PropertyCard({
  property,
}: PropertyCardProps) {
  return (
    <article className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3">
        <h3 className="font-semibold text-gray-900">
          {property.title ?? `Imóvel em ${property.neighborhood}`}
        </h3>

        <p className="text-sm text-gray-500">
          {property.neighborhood}
        </p>
      </div>

      <p className="mb-3 text-lg font-semibold text-blue-600">
        {formatPrice(property.price)}
      </p>

      <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-gray-600">
        <span>{property.bedrooms} quartos</span>

        <span>{property.bathrooms} banheiros</span>

        <span>{property.usable_area} m²</span>

        {property.parking_spaces !== null && (
          <span>{property.parking_spaces} vagas</span>
        )}
      </div>

      <p className="mt-3 text-xs text-gray-500">
        Compatibilidade: {formatSimilarity(property.similarity_score)}
      </p>
    </article>
  );
}