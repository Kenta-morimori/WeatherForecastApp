"use client";

import { SearchForm } from "@/components/search-form";
import { ResultCard } from "@/components/result-card";
import { useState } from "react";

export default function Page() {
  const [mock, setMock] = useState<{
    locationLabel?: string;
    tempMean?: number;
    tempMin?: number;
    tempMax?: number;
    precipMm?: number;
  } | null>(null);

  return (
    <main className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">WeatherForecastApp</h1>
        <p className="text-sm text-muted-foreground">
          地点を指定して <strong>「明日の気温・降水」</strong> を表示する MVP（モック）。
        </p>
      </header>

      <SearchForm
        onSubmit={(payload) => {
          // --- モック値（本実装では /api/predict を叩く） ---
          const label =
            payload.name?.trim() ||
            `${Number(payload.lat).toFixed(3)}, ${Number(payload.lon).toFixed(3)}`;
          setMock({
            locationLabel: label,
            tempMean: 26.8,
            tempMin: 23.1,
            tempMax: 30.4,
            precipMm: 4.6,
          });
        }}
      />

      {mock && (
        <ResultCard
          locationLabel={mock.locationLabel!}
          tempMean={mock.tempMean!}
          tempMin={mock.tempMin!}
          tempMax={mock.tempMax!}
          precipMm={mock.precipMm!}
        />
      )}
    </main>
  );
}
