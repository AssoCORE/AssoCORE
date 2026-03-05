import Link from "next/link";

export default function profile() {
  return (
    <div style={{ padding: 40 }}>
      <h1>Bienvenue sur l'autre page</h1>

      <Link href="/">
        <button>Retour à l'accueil</button>
      </Link>
    </div>
  );
}
