export function BoardSkeleton() {
  return (
    <div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-3" aria-busy="true" aria-label="Loading tasks">
      {["To Do", "In Progress", "Done"].map((label) => (
        <section key={label} className="glass-panel rounded-2xl p-4">
          <div className="mb-4 flex items-center gap-2 px-1">
            <span className="size-2.5 animate-pulse-soft rounded-full bg-slate-300" />
            <span className="h-3.5 w-20 animate-pulse-soft rounded bg-slate-200" />
          </div>
          <div className="space-y-3">
            {[0, 1].map((i) => (
              <div key={i} className="glass-card rounded-xl p-4">
                <div className="h-3.5 w-2/3 animate-pulse-soft rounded bg-slate-200" />
                <div className="mt-3 h-2.5 w-full animate-pulse-soft rounded bg-slate-100" />
                <div className="mt-1.5 h-2.5 w-4/5 animate-pulse-soft rounded bg-slate-100" />
                <div className="mt-4 h-2.5 w-1/3 animate-pulse-soft rounded bg-slate-100" />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export function BoardError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="glass-panel mt-6 flex flex-col items-center rounded-2xl px-6 py-16 text-center">
      <h2 className="font-display text-lg font-bold text-ink">Couldn't load your board</h2>
      <p className="mt-2 max-w-sm text-sm text-slate-soft">
        The task service didn't respond. Check your connection and try again.
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-5 rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:bg-brand-strong"
      >
        Retry
      </button>
    </div>
  );
}
