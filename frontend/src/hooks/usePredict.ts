import { type PredictInput, type PredictResponse, fetchPredict } from '@/lib/api';
import { useQuery } from '@tanstack/react-query';

export function usePredict(input: PredictInput | null) {
	return useQuery<PredictResponse, Error>({
		queryKey: ['predict', input?.lat, input?.lon, input?.tz],
		queryFn: ({ signal }) => {
			if (!input) throw new Error('Missing input');
			return fetchPredict(input, signal);
		},
		enabled: !!input,
	});
}
