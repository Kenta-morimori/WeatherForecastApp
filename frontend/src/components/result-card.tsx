import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ResultCard(props: {
  locationLabel: string;
  tempMean: number;
  tempMin: number;
  tempMax: number;
  precipMm: number;
}) {
  const { locationLabel, tempMean, tempMin, tempMax, precipMm } = props;
  return (
    <Card>
      <CardHeader>
        <CardTitle>予測結果（モック）</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        <div>
          <span className="text-muted-foreground">地点：</span>
          <span className="font-medium">{locationLabel}</span>
        </div>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          <Stat label="平均気温" value={`${tempMean.toFixed(1)} ℃`} />
          <Stat label="最低気温" value={`${tempMin.toFixed(1)} ℃`} />
          <Stat label="最高気温" value={`${tempMax.toFixed(1)} ℃`} />
          <Stat label="降水量" value={`${precipMm.toFixed(1)} mm`} />
        </div>
        <p className="text-muted-foreground">
          ※ 現在は固定のダミー値です。実装時は /api/predict を呼び出します。
        </p>
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border bg-card p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-base font-semibold">{value}</div>
    </div>
  );
}
