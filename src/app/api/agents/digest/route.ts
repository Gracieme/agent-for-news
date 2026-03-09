import { NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET() {
  if (!supabase) {
    return NextResponse.json(
      { error: "未配置 Supabase" },
      { status: 503 }
    );
  }
  try {
    const { data, error } = await supabase
      .from("agent_digests")
      .select("date, digest")
      .order("date", { ascending: false })
      .limit(1)
      .maybeSingle();

    if (error) throw error;
    if (!data) {
      return NextResponse.json({
        date: null,
        digest: null,
        message: "暂无推送，请先运行 agent-squad 并配置 Supabase 同步",
      });
    }
    return NextResponse.json({
      date: data.date,
      digest: data.digest,
    });
  } catch (e) {
    console.error("Agent digest fetch error:", e);
    return NextResponse.json(
      { error: "获取失败" },
      { status: 500 }
    );
  }
}
