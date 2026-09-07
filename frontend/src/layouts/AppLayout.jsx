import "../styles/AppLayout.css";

export default function AppLayout({ left, right }) {
  return (
    <div className="crm-layout">
      <main className="crm-main">
        <section className="workspace-panel">{left}</section>

        <aside className="assistant-panel">{right}</aside>
      </main>
    </div>
  );
}
