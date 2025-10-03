// src/components/prediction-chart.tsx
import {
	Legend,
	Line,
	LineChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";

export type ChartPoint = {
	date: string;
	predicted?: number | null;
	actual?: number | null;
};

function fmtTooltipValue(v: unknown) {
	if (v === null || v === undefined) return "-";
	const n = Number(v);
	return Number.isNaN(n) ? "-" : n;
}

export function PredictionChart({ data }: { data: ChartPoint[] }) {
	return (
		<div className="w-full h-64 sm:h-80 rounded-2xl border p-3">
			<div className="text-sm mb-2 opacity-70">予測と直近実績（気温）</div>
			<ResponsiveContainer width="100%" height="100%">
				<LineChart
					data={data}
					margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
				>
					<XAxis dataKey="date" tick={{ fontSize: 12 }} minTickGap={24} />
					<YAxis tick={{ fontSize: 12 }} domain={["auto", "auto"]} />
					<Tooltip formatter={(value) => fmtTooltipValue(value)} />
					<Legend />
					<Line
						type="monotone"
						dataKey="actual"
						name="実績"
						dot={false}
						strokeWidth={2}
						connectNulls
					/>
					<Line
						type="monotone"
						dataKey="predicted"
						name="予測"
						dot={false}
						strokeWidth={2}
						connectNulls
					/>
				</LineChart>
			</ResponsiveContainer>
		</div>
	);
}
