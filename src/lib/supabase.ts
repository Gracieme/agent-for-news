import { createClient, SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

export const supabase: SupabaseClient | null =
  supabaseUrl && supabaseAnonKey && supabaseUrl.startsWith("http")
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null;

export interface Reading {
  id?: string;
  user_id: string;
  spread_type: string;
  question: string;
  cards: { id: number; nameZh: string; reversed: boolean; position: string }[];
  interpretation: string;
  created_at?: string;
}
