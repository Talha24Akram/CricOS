import Link from "next/link";

export function Nav() {
  return (
    <nav className="nav">
      <Link href="/">Home</Link>
      <Link href="/live">Live</Link>
      <Link href="/scorecard">Scorecard</Link>
      <Link href="/tournament">Tournament</Link>
      <Link href="/prediction">Prediction</Link>
      <Link href="/player/1">Player Profile</Link>
    </nav>
  );
}
