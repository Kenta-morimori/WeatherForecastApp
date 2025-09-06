import { z } from "zod";

// name か lat/lon のどちらか一方は必須
export const zLocation = z
  .object({
    name: z.string().trim().optional().default(""),
    lat: z.union([z.string(), z.number()]).optional(),
    lon: z.union([z.string(), z.number()]).optional(),
  })
  .refine(
    (v) => {
      const hasName = !!v.name && v.name.trim().length > 0;
      const hasCoords = v.lat !== undefined && v.lon !== undefined && `${v.lat}` !== "" && `${v.lon}` !== "";
      return hasName || hasCoords;
    },
    { message: "地名 または 緯度・経度のどちらかを入力してください。" },
  )
  .transform((v) => ({
    name: (v.name ?? "").trim(),
    lat: v.lat === undefined || v.lat === "" ? "" : Number(v.lat),
    lon: v.lon === undefined || v.lon === "" ? "" : Number(v.lon),
  }));
