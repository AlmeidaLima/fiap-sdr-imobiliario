# Frontend — Agente SDR Imobiliário

Interface Next.js da POC do Hackathon FIAP. Disponibiliza:

- Chat em `/`, com qualificação, imóveis, seleção, agendamento, handoff, histórico persistido e polling de mensagens;
- Dashboard em `/dashboard`, somente leitura, para acompanhamento dos leads.

## Tecnologias

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- Vitest e Testing Library

## Execução local

```bash
npm ci
npm run dev
```

Por padrão, o frontend fica em <http://localhost:3000> e usa `http://localhost:8000` como endereço público da API quando `NEXT_PUBLIC_API_URL` não está definido.

## Validação

```bash
npm run test:run
npm run lint
npm run build
```

Para executar a solução completa, preparar banco, migrations, imóveis, embeddings e worker, siga o [README principal](../README.md). Consulte também a [arquitetura](../docs/ARCHITECTURE.md) e a [rastreabilidade dos requisitos](../docs/TRACEABILITY.md).
