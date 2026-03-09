import { SignIn } from "@clerk/nextjs";

const afterSignInUrl = process.env.NEXT_PUBLIC_APP_URL
  ? `${process.env.NEXT_PUBLIC_APP_URL.replace(/\/$/, "")}/`
  : "/";

export default function SignInPage() {
  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 50%, #F5F2EC 100%)" }}
    >
      <div className="text-center">
        <div className="text-5xl mb-6">☽</div>
        <h1 className="text-3xl font-bold mb-8" style={{ color: "var(--text-warm)" }}>
          欢迎回来
        </h1>
        <SignIn
          fallbackRedirectUrl={afterSignInUrl}
          forceRedirectUrl={afterSignInUrl}
        />
      </div>
    </div>
  );
}
