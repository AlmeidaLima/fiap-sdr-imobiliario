import type { PropertySearchResponse } from "../../types/property";

interface PropertyCardProps {
  property: PropertySearchResponse;
}

function formatQuantity(
    quantity: number,
    singular: string,
    plural: string,
): string {
    return `${quantity} ${quantity === 1 ? singular : plural}`;
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
        <article className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
            <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                    <h3
                        className="line-clamp-2 font-semibold leading-snug text-gray-900"
                        title={
                            property.title ??
                            `Imóvel em ${property.neighborhood}`
                        }
                    >
                        {property.title ??
                            `Imóvel em ${property.neighborhood}`}
                    </h3>

                    <p className="mt-1 text-sm text-gray-500">
                        {property.neighborhood}
                    </p>
                </div>

                <span className="shrink-0 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
        {formatSimilarity(property.similarity_score)}
      </span>
            </div>

            <p className="mt-4 text-xl font-bold text-blue-600">
                {formatPrice(property.price)}
            </p>

            <div className="mt-4 flex flex-wrap gap-2 text-sm text-gray-600">
      <span className="rounded-lg bg-gray-50 px-3 py-2">
        {formatQuantity(property.bedrooms, "quarto", "quartos")}
      </span>

                <span className="rounded-lg bg-gray-50 px-3 py-2">
        {formatQuantity(
            property.bathrooms,
            "banheiro",
            "banheiros",
        )}
      </span>

                <span className="rounded-lg bg-gray-50 px-3 py-2">
        {property.usable_area} m²
      </span>

                {property.parking_spaces !== null && (
                    <span className="rounded-lg bg-gray-50 px-3 py-2">
          {formatQuantity(
              property.parking_spaces,
              "vaga",
              "vagas",
          )}
        </span>
                )}
            </div>

            <p className="mt-4 text-xs text-gray-500">
                Compatibilidade com sua busca
            </p>
        </article>
    );
}