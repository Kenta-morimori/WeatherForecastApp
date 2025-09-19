"use client";

// 既存の呼び出し `const { toast } = useToast()` と互換をもたせる薄いラッパ
import { toast as sonner } from "sonner";

export function useToast() {
  return { toast: sonner };
}
