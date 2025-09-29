import GeoPredictClient from './GeoPredictClient';

export const dynamic = 'force-dynamic'; // 開発時のSSRキャッシュ抑止（任意）

export default function Page() {
	return <GeoPredictClient />;
}
