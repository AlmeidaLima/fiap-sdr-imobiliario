type HealthResponse = {
  status: string;
  service: string;
};

async function getBackendHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch("http://backend:8000/health", {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await getBackendHealth();

  return (
      <main
          style={{
            padding: "40px",
            fontFamily: "Arial, sans-serif",
          }}
      >
        <h1>Agente SDR Imobiliário</h1>

        <h2>Status do Backend</h2>

        {health ? (
            <div>
              <p>
                <strong>Status:</strong> {health.status}
              </p>

              <p>
                <strong>Serviço:</strong> {health.service}
              </p>

              <p>✅ Frontend conectado ao backend.</p>
            </div>
        ) : (
            <p>❌ Não foi possível conectar ao backend.</p>
        )}
      </main>
  );
}