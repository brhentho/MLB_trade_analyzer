import type { ReactNode } from "react";

export function LoadingRows({ label, rows = 6 }: { label: string; rows?: number }) {
  return (
    <div role="status" aria-live="polite" className="space-y-2 py-2">
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-6 rounded-sm bg-surface-2" style={{ opacity: 1 - i * 0.12 }} />
      ))}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded border border-bad/50 bg-bad/10 px-4 py-3 text-sm">
      <p className="font-semibold text-ink">Couldn&apos;t load this data.</p>
      <p className="mt-1 text-ink-2">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 min-h-10 rounded border border-line bg-surface px-3 text-sm font-semibold hover:bg-surface-2"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded border border-dashed border-line px-4 py-6 text-center text-sm">
      <p className="font-semibold">{title}</p>
      {children && <div className="mt-1 text-ink-2">{children}</div>}
    </div>
  );
}
