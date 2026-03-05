import Link from "next/link";

export default function Home() {
  return (
    <div style={{ padding: 40 }}>
      <h1>Page principale</h1>

      <Link href="/profile">
        <button>Aller à la page de profile</button>
      </Link>
      <Link href="/event">
        <button>Aller à la page d'evenement</button>
      </Link>
      <Link href="/calendar">
        <button>Aller à la page de calendrier</button>
      </Link>
      <Link href="/file">
        <button>Aller à la page de fichier</button>
      </Link>
      <Link href="/adminUser">
        <button>Aller à la page d'amin pour les profile</button>
      </Link>
      <Link href="/adminEvent">
        <button>Aller à la page d'admin pour les event</button>
      </Link>
    </div>
  );
}
