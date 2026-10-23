import Link from "next/link";

export default function NotFound() {
  return (
    <main className="wrap flex-1 w-full pt-16">
      <h1 className="display" style={{ fontSize: "3rem", margin: 0 }}>
        No chart here
      </h1>
      <p className="lead mt-3">
        The link may be old or mistyped. <Link href="/">See every chart</Link>.
      </p>
    </main>
  );
}
