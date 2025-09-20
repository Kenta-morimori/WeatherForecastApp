// frontend/app/page.tsx
import { redirect } from 'next/navigation';

export default function Page() {
	// ルートに来たら /forecast に送る
	redirect('/forecast');
}
