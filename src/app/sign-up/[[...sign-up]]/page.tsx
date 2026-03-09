import { SignUp } from "@clerk/nextjs";

const afterSignUpUrl = process.env.NEXT_PUBLIC_APP_URL
  ? `${process.env.NEXT_PUBLIC_APP_URL.replace(/\/$/, "")}/`
  : "/";

export default function SignUpPage() {
  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 50%, #F5F2EC 100%)" }}
    >
      <div className="text-center">
        <div className="text-5xl mb-6">☽</div>
        <h1 className="text-3xl font-bold mb-8" style={{ color: "var(--text-warm)" }}>
          开启你的星语之旅
        </h1>
        <SignUp
          fallbackRedirectUrl={afterSignUpUrl}
          forceRedirectUrl={afterSignUpUrl}
        />
      </div>
    </div>
  );
}
