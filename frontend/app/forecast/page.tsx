'use client';

import { ResultCard } from '@/components/result-card';
import { SearchForm, type SearchFormPayload } from '@/components/search-form';
import { useState } from 'react';

type Mock = {
	locationLabel: string;
	tempMean: number;
	tempMin: number;
	tempMax: number;
	precipMm: number;
};

export default function Page() {
	const [mock, setMock] = useState<Mock | null>(null);

	return (
		<main className="space-y-6 p-4">
			<SearchForm
				onSubmit={(payload: SearchFormPayload) => {
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
					locationLabel={mock.locationLabel}
					tempMean={mock.tempMean}
					tempMin={mock.tempMin}
					tempMax={mock.tempMax}
					precipMm={mock.precipMm}
				/>
			)}
		</main>
	);
}
