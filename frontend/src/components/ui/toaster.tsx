"use client";

import { Toaster as SonnerToaster } from "sonner";

export function Toaster() {
  // お好みで位置や色を調整可能
  return <SonnerToaster position="top-right" richColors closeButton />;
}

export default Toaster;
