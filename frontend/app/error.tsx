"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="empty-state" role="alert">
      <h1>This view could not be displayed</h1>
      <p>Please retry. Saved scenarios remain in the database.</p>
      <button onClick={reset}>Retry view</button>
    </div>
  );
}
