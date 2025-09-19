"use client";

import React from "react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { cn } from "@/lib/utils";

// ===== 型：バックエンド生レスポンス（2025-09-19 実測に基づく） =====
type BackendResponse = {
  d0: { max: number; min: number; precip_prob: number; precip: number };
  d1: { max: number; min: number; precip_prob: number; precip: number };
  forecast_series: Array<Record<string, unknown>>;
  recent_actuals: Array<Record<string, unknown>>;
};

// ===== UI用型（カード/グラフ表示用に正規化） =====
export type DaySummary = {
  date?: string;           // バックエンドに無ければフロントで補完
  max: number;             // 最高気温 [℃]
  min: number;             // 最低気温 [℃]
  pop: number;             // 降水確率 [0..1]
  precip: number;          // 降水量 [mm]
};

export type SeriesPoint = {
  date: string;            // YYYY-MM-DD
  pred?: number;           // 予測（例：平均気温）
  actual?: number;         // 直近実績（存在しない日もある）
};

export type PredictResponse = {
  location: {
    name: string;
    tz: string;
  };
  d0: DaySummary;          // 今日（TZ基準）or リクエスト起点日
  d1: DaySummary;          // 翌日
  series: SeriesPoint[];   // 予測 vs 実績の線
};

// ===== API base (環境に合わせて変更) =====
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"; // FastAPI 既定

// ===== Utils: 日付補完（TZ基準で D0/D1 を作る） =====
function toISODateInTZ(d: Date, tz: string) {
  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const parts = fmt.formatToParts(d).reduce<Record<string, string>>((acc, p) => {
    acc[p.type] = p.value;
    return acc;
  }, {});
  return `${parts.year}-${parts.month}-${parts.day}`;
}
function computeD0D1Dates(tz: string) {
  const now = new Date();
  const d0 = toISODateInTZ(now, tz);
  const d1 = toISODateInTZ(new Date(now.getTime() + 24 * 60 * 60 * 1000), tz);
  return { d0, d1 };
}
function coerceNumber(x: unknown): number | undefined {
  if (typeof x === "number" && Number.isFinite(x)) return x;
  if (typeof x === "string") {
    const n = Number(x);
    if (Number.isFinite(n)) return n;
  }
  return undefined;
}

// ===== Helpers =====
function formatPop(pop: number) {
  const v = Math.max(0, Math.min(1, pop ?? 0));
  return `${Math.round(v * 100)}%`;
}
function formatPrecip(mm: number) {
  return `${mm.toFixed(1)} mm`;
}

// ===== 正規化：BackendResponse -> PredictResponse =====
function normalizeResponse(raw: BackendResponse, params: { q: string; tz: string }): PredictResponse {
  const { d0, d1, forecast_series, recent_actuals } = raw;
  const { d0: d0Date, d1: d1Date } = computeD0D1Dates(params.tz);

  const normD0: DaySummary = {
    date: d0Date,
    max: d0.max,
    min: d0.min,
    pop: d0.precip_prob,
    precip: d0.precip,
  };
  const normD1: DaySummary = {
    date: d1Date,
    max: d1.max,
    min: d1.min,
    pop: d1.precip_prob,
    precip: d1.precip,
  };

  // グラフ統合: {date, value} 形式をゆるく想定（無ければ空のまま）
  const mapSeries = (arr: Array<Record<string, unknown>>) =>
    arr
      .map((o) => {
        const date = String(o["date"] ?? "");
        const v = coerceNumber(o["value"] ?? o["temp"] ?? o["mean"] ?? o["pred"]);
        if (!date || v === undefined) return null;
        return { date, value: v };
      })
      .filter(Boolean) as { date: string; value: number }[];

  const preds = mapSeries(forecast_series);
  const acts = mapSeries(recent_actuals);

  const byDate = new Map<string, SeriesPoint>();
  for (const p of preds) byDate.set(p.date, { date: p.date, pred: p.value });
  for (const a of acts)
    byDate.set(a.date, { ...(byDate.get(a.date) ?? { date: a.date }), actual: a.value });

  const series = Array.from(byDate.values()).sort((a, b) => a.date.localeCompare(b.date));

  return {
    location: { name: params.q || "(unknown)", tz: params.tz },
    d0: normD0,
    d1: normD1,
    series,
  };
}

// ===== Geocoding (Open-Meteo, API key不要) =====
async function geocode(q: string) {
  const url = new URL("https://geocoding-api.open-meteo.com/v1/search");
  url.searchParams.set("name", q);
  url.searchParams.set("count", "1");
  url.searchParams.set("language", "ja");
  url.searchParams.set("format", "json");

  const res = await fetch(url.toString());
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Geocoding failed ${res.status}: ${text}`);
  }
  const data = (await res.json()) as {
    results?: Array<{ latitude: number; longitude: number; name?: string; country?: string }>;
  };
  const first = data.results?.[0];
  if (!first) throw new Error(`地点を特定できませんでした: "${q}"`);
  return {
    lat: first.latitude,
    lon: first.longitude,
    resolvedName: `${first.name ?? q}${first.country ? `, ${first.country}` : ""}`,
  };
}

// ===== Fetcher（geocode → /predict 呼び出し → 正規化） =====
async function fetchPredict(params: { q: string; tz: string }) {
  // 1) 都市名から緯度経度へ（Open-Meteo Geocoding）
  const { lat, lon, resolvedName } = await geocode(params.q);

  // 2) 予測API呼び出し
  const url = new URL("/predict", API_BASE);
  url.searchParams.set("lat", String(lat));
  url.searchParams.set("lon", String(lon));
  url.searchParams.set("tz", params.tz);

  const res = await fetch(url.toString(), { next: { revalidate: 0 } });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Server responded ${res.status}: ${text}`);
  }
  const raw: BackendResponse = await res.json();
  const normalized = normalizeResponse(raw, params);
  // 取得した正規化データに地名（整形済み）を反映
  return { ...normalized, location: { ...normalized.location, name: resolvedName } };
}

// ===== Result Card =====
function ResultCard({ title, day }: { title: string; day: DaySummary }) {
  return (
    <Card className="rounded-2xl shadow-sm">
      <CardHeader>
        <CardTitle className="text-base sm:text-lg">
          {title}
          {day.date ? `（${day.date}）` : ""}
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 text-sm sm:text-base">
        <div className="space-y-1">
          <div className="text-muted-foreground">最高</div>
          <div className="font-semibold">{day.max.toFixed(1)}℃</div>
        </div>
        <div className="space-y-1">
          <div className="text-muted-foreground">最低</div>
          <div className="font-semibold">{day.min.toFixed(1)}℃</div>
        </div>
        <div className="space-y-1">
          <div className="text-muted-foreground">降水確率</div>
          <div className="font-semibold">{formatPop(day.pop)}</div>
        </div>
        <div className="space-y-1">
          <div className="text-muted-foreground">降水量</div>
          <div className="font-semibold">{formatPrecip(day.precip)}</div>
        </div>
      </CardContent>
    </Card>
  );
}

// ===== Chart =====
function ForecastChart({ data }: { data: SeriesPoint[] }) {
  if (!data?.length) {
    return (
      <div className="rounded-2xl border p-4 text-sm text-muted-foreground">
        グラフ用データがありません（backend: forecast_series / recent_actuals が空）。
      </div>
    );
  }
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 16, right: 24, bottom: 8, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} angle={0} height={40} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="pred" name="予測" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="actual" name="実績" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ===== Form + Results =====
function ForecastContent() {
  const { toast } = useToast();
  const [q, setQ] = React.useState("Tokyo");           // 入力（都市名）
  const [tz, setTz] = React.useState("Asia/Tokyo");
  const [openErr, setOpenErr] = React.useState(false);

  const query = useQuery({
    queryKey: ["predict", { q, tz }],
    queryFn: () => fetchPredict({ q, tz }),
    enabled: false, // submit まで走らない
    retry: 1,
  });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await query.refetch();
    } catch {
      // refetch 経由の throw はここには来ないが保険として
    }
  };

  React.useEffect(() => {
    if (query.isError) {
      const message = query.error instanceof Error ? query.error.message : "Unknown error";
      toast({ title: "取得に失敗した", description: message, variant: "destructive" });
      setOpenErr(true);
    }
  }, [query.isError, query.error, toast]);

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 sm:p-6">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">天気予測</h1>
        <p className="text-sm text-muted-foreground">フロントから推論APIを呼び出して可視化するフェーズ</p>
      </div>

      {/* Form */}
      <form onSubmit={onSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_auto]">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <div className="space-y-1">
            <Label htmlFor="q">地点（都市名など）</Label>
            <Input
              id="q"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Tokyo / Fukuoka / Seoul / New York"
              required
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="tz">タイムゾーン</Label>
            <Input id="tz" value={tz} onChange={(e) => setTz(e.target.value)} placeholder="Asia/Tokyo" />
          </div>
        </div>
        <div className="flex items-end">
          <Button
            type="submit"
            className={cn("w-full sm:w-auto", query.isFetching && "pointer-events-none opacity-70")}
          >
            {query.isFetching ? "問い合わせ中…" : "予測する"}
          </Button>
        </div>
      </form>

      {/* Loading */}
      {query.isFetching && (
        <div className="animate-pulse rounded-2xl border p-6 text-sm text-muted-foreground">
          推論APIに問い合わせています…
        </div>
      )}

      {/* Results */}
      {query.data && (
        <div className="space-y-6">
          <div className="text-sm text-muted-foreground">
            対象: {query.data.location.name}（TZ: {query.data.location.tz}）
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <ResultCard title="D0" day={query.data.d0} />
            <ResultCard title="D1" day={query.data.d1} />
          </div>

          <Card className="rounded-2xl">
            <CardHeader>
              <CardTitle className="text-base sm:text-lg">予測と直近実績（線）</CardTitle>
            </CardHeader>
            <CardContent>
              <ForecastChart data={query.data.series} />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Error dialog */}
      <Dialog open={openErr} onOpenChange={setOpenErr}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>エラーが発生した</DialogTitle>
            <DialogDescription className="whitespace-pre-wrap">
              {query.error instanceof Error ? query.error.message : "Unknown error"}
            </DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ===== Page Wrapper (ensure providers exist at app root or here) =====
const queryClient = new QueryClient();

export default function ForecastPage() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* shadcn/ui の <Toaster /> は layout.tsx に配置 */}
      <ForecastContent />
    </QueryClientProvider>
  );
}
