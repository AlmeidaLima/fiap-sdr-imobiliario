"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import {
  getDashboardLead,
  getDashboardLeads,
} from "../../services/dashboardService";
import type {
  DashboardLeadDetailResponse,
  DashboardLeadSummary,
} from "../../types/dashboard";
import { LeadDetails } from "./LeadDetails";
import { LeadList } from "./LeadList";

export function Dashboard() {
  const [leads, setLeads] = useState<DashboardLeadSummary[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<number | null>(null);
  const [detail, setDetail] = useState<DashboardLeadDetailResponse | null>(null);
  const [listLoading, setListLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [listError, setListError] = useState(false);
  const [detailError, setDetailError] = useState(false);
  const detailRequestToken = useRef(0);

  async function loadLeads() {
    setListLoading(true);
    setListError(false);
    try {
      const response = await getDashboardLeads();
      setLeads(response.leads);
    } catch {
      setListError(true);
    } finally {
      setListLoading(false);
    }
  }

  async function selectLead(leadId: number) {
    const requestToken = ++detailRequestToken.current;
    setSelectedLeadId(leadId);
    setDetail(null);
    setDetailLoading(true);
    setDetailError(false);
    try {
      const response = await getDashboardLead(leadId);
      if (requestToken === detailRequestToken.current) {
        setDetail(response);
      }
    } catch {
      if (requestToken === detailRequestToken.current) {
        setDetailError(true);
      }
    } finally {
      if (requestToken === detailRequestToken.current) {
        setDetailLoading(false);
      }
    }
  }

  useEffect(() => {
    let active = true;

    void getDashboardLeads()
      .then((response) => {
        if (active) setLeads(response.leads);
      })
      .catch(() => {
        if (active) setListError(true);
      })
      .finally(() => {
        if (active) setListLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 p-4 sm:p-6">
      <div className="mx-auto max-w-7xl">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-4 text-white shadow-sm">
          <div>
            <h1 className="text-xl font-semibold">Dashboard de Leads</h1>
            <p className="mt-1 text-sm text-blue-100">Acompanhamento comercial dos atendimentos da LIA</p>
          </div>
          <Link href="/" className="rounded-lg bg-white/15 px-4 py-2 text-sm font-semibold ring-1 ring-white/30 hover:bg-white/25">
            Voltar ao atendimento
          </Link>
        </header>

        <div className="grid gap-5 lg:grid-cols-[22rem_minmax(0,1fr)]">
          <section aria-labelledby="lead-list-title" className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-4 py-3">
              <h2 id="lead-list-title" className="font-semibold text-slate-900">Leads</h2>
            </div>
            {listLoading && <p role="status" className="p-4 text-sm text-slate-500">Carregando leads...</p>}
            {listError && (
              <div role="alert" className="p-4 text-sm text-red-700">
                <p>Não foi possível carregar os leads.</p>
                <button type="button" onClick={() => void loadLeads()} className="mt-2 font-semibold underline">Tentar novamente</button>
              </div>
            )}
            {!listLoading && !listError && leads.length === 0 && (
              <p className="p-4 text-sm text-slate-500">Nenhum lead disponível.</p>
            )}
            {!listLoading && !listError && leads.length > 0 && (
              <LeadList leads={leads} selectedLeadId={selectedLeadId} onSelect={(leadId) => void selectLead(leadId)} />
            )}
          </section>

          <section aria-labelledby="lead-details-title" className="min-w-0">
            <h2 id="lead-details-title" className="sr-only">Detalhes do lead</h2>
            {selectedLeadId === null && (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-slate-500">
                Selecione um lead para visualizar os detalhes.
              </div>
            )}
            {detailLoading && <div role="status" className="rounded-2xl bg-white p-5 text-sm text-slate-500">Carregando detalhes...</div>}
            {detailError && selectedLeadId !== null && (
              <div role="alert" className="rounded-2xl bg-white p-5 text-sm text-red-700">
                <p>Não foi possível carregar os detalhes do lead.</p>
                <button type="button" onClick={() => void selectLead(selectedLeadId)} className="mt-2 font-semibold underline">Tentar novamente</button>
              </div>
            )}
            {detail && !detailLoading && !detailError && <LeadDetails detail={detail} />}
          </section>
        </div>
      </div>
    </main>
  );
}
