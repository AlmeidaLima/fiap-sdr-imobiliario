import type { PropertySearchResponse } from "../../types/property";
import { PropertyCard } from "./PropertyCard";

interface PropertyListProps {
  properties: PropertySearchResponse[];
}

export function PropertyList({
  properties,
}: PropertyListProps) {
  if (properties.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3 px-4 pb-4">
      <div>
        <h2 className="font-semibold text-gray-900">
          Imóveis encontrados
        </h2>

        <p className="text-sm text-gray-500">
          Encontrei algumas opções que combinam com sua busca.
        </p>
      </div>

      <div className="grid gap-3">
        {properties.map((property) => (
          <PropertyCard
            key={property.id}
            property={property}
          />
        ))}
      </div>
    </div>
  );
}