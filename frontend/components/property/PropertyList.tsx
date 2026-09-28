import type { PropertySearchResponse } from "../../types/property";
import { PropertyCard } from "./PropertyCard";

interface PropertyListProps {
  properties: PropertySearchResponse[];
  showNoResults?: boolean;
  onSelect?: (propertyId: number) => void;
  selectedPropertyId?: number | null;
  appointmentPersisted?: boolean;
  selectionDisabled?: boolean;
}

export function PropertyList({
  properties,
  showNoResults = false,
  onSelect,
  selectedPropertyId = null,
  appointmentPersisted = false,
  selectionDisabled = false,
}: PropertyListProps) {
    if (properties.length === 0) {
        if (showNoResults) {
            return (
                <div className="flex h-full items-center justify-center bg-slate-50/50 p-8">
                    <p className="text-center text-sm text-slate-600">
                        Nenhum imóvel encontrado para os critérios atuais.
                    </p>
                </div>
            );
        }

        return (
            <div className="flex h-full items-center justify-center bg-slate-50/50 p-8">
                <div className="max-w-md text-center">
                    <div
                        className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100"
                        aria-hidden="true"
                    >
                        <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            className="h-8 w-8 text-indigo-600"
                            stroke="currentColor"
                            strokeWidth="1.8"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M3 11.5 12 4l9 7.5"
                            />
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M5.5 10.5V20h13v-9.5"
                            />
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M9.5 20v-5.5h5V20"
                            />
                        </svg>
                    </div>

                    <h2 className="text-lg font-semibold text-slate-900">
                        Encontre seu imóvel ideal
                    </h2>

                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                        Converse com a LIA sobre localização, orçamento e
                        características desejadas.
                    </p>

                    <p className="mt-1 text-sm font-medium text-indigo-600">
                        As melhores opções aparecerão aqui.
                    </p>
                </div>
            </div>
        );
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
            onSelect={onSelect}
            isSelected={selectedPropertyId === property.id}
            appointmentPersisted={
              appointmentPersisted && selectedPropertyId === property.id
            }
            selectionDisabled={selectionDisabled}
          />
        ))}
      </div>
    </div>
  );
}
