'use client';
import * as React from 'react';

type Toast = {
  id: number;
  title: string;
  description?: string;
  variant?: 'default' | 'destructive';
};

type ToastContext = {
  toast: (t: Omit<Toast, 'id'>) => void;
};

const ToastCtx = React.createContext<ToastContext | null>(null);

/**
 * アプリ全体のトーストを管理する Provider。
 * children を包むだけで OK。任意の場所で useToast().toast(...) を呼べます。
 */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [seq, setSeq] = React.useState(0);
  const [items, setItems] = React.useState<Toast[]>([]);

  const value = React.useMemo<ToastContext>(
    () => ({
      toast: (t: Omit<Toast, 'id'>) => {
        // 採番は関数型更新で競合を回避しつつ、その場で id を確定させる
        let newId = 0;
        setSeq((s) => {
          const next = s + 1;
          newId = next;
          return next;
        });
        setItems((xs) => [...xs, { id: newId, ...t }]);

        // 3秒後に該当トーストだけを除去
        setTimeout(() => {
          setItems((xs) => xs.filter((x) => x.id !== newId));
        }, 3000);
      },
    }),
    [],
  );

  return (
    <ToastCtx.Provider value={value}>
      {children}
      {/* トースト描画（単一ソースに集約） */}
      <div className="fixed right-4 top-4 z-50 space-y-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={`min-w-[260px] rounded-2xl px-4 py-3 text-sm shadow-lg ${
              t.variant === 'destructive' ? 'bg-red-600 text-white' : 'bg-gray-900 text-white'
            }`}
          >
            <div className="font-semibold">{t.title}</div>
            {t.description && <div className="opacity-90">{t.description}</div>}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

/** トースト用フック。Provider 外では no-op を返すフォールバック。 */
export function useToast() {
  const ctx = React.useContext(ToastCtx);
  if (!ctx) return { toast: () => {} };
  return ctx;
}
