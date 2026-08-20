import { clientApi } from "@/lib/client-api";
import type { MediaAsset } from "@/lib/types";

type UploadProgress = { completedParts: number; totalParts: number; percent: number };

export async function uploadMediaFile(
  file: File,
  onProgress?: (progress: UploadProgress) => void,
): Promise<MediaAsset> {
  const initiated = await clientApi<MediaAsset>("/uploads/initiate/", {
    method: "POST",
    body: JSON.stringify({
      original_name: file.name,
      content_type: file.type || "application/octet-stream",
      size_bytes: file.size,
    }),
  });

  const partCount = initiated.part_count ?? 1;
  const partSize = initiated.part_size ?? file.size;
  const signedUrls = new Map<number, string>();

  for (let start = 1; start <= partCount; start += 100) {
    const partNumbers = Array.from(
      { length: Math.min(100, partCount - start + 1) },
      (_, index) => start + index,
    );
    const signed = await clientApi<{ parts: Array<{ part_number: number; url: string }> }>(
      `/uploads/${initiated.id}/parts/sign/`,
      { method: "POST", body: JSON.stringify({ part_numbers: partNumbers }) },
    );
    for (const part of signed.parts) signedUrls.set(part.part_number, part.url);
  }

  const completed: Array<{ part_number: number; etag: string }> = [];
  let nextPart = 1;
  let completedParts = 0;

  async function worker() {
    while (true) {
      const partNumber = nextPart++;
      if (partNumber > partCount) return;
      const url = signedUrls.get(partNumber);
      if (!url) throw new Error(`Не получена ссылка для части ${partNumber}.`);
      const start = (partNumber - 1) * partSize;
      const end = Math.min(start + partSize, file.size);
      const response = await fetch(url, {
        method: "PUT",
        body: file.slice(start, end),
      });
      if (!response.ok) throw new Error(`Не удалось загрузить часть ${partNumber}.`);
      const etag = response.headers.get("etag") ?? response.headers.get("ETag");
      if (!etag) throw new Error("Object storage не вернул ETag для загруженной части.");
      completed.push({ part_number: partNumber, etag });
      completedParts += 1;
      onProgress?.({
        completedParts,
        totalParts: partCount,
        percent: Math.round((completedParts / partCount) * 100),
      });
    }
  }

  try {
    await Promise.all(Array.from({ length: Math.min(3, partCount) }, () => worker()));
    completed.sort((a, b) => a.part_number - b.part_number);
    return await clientApi<MediaAsset>(`/uploads/${initiated.id}/complete/`, {
      method: "POST",
      body: JSON.stringify({ parts: completed }),
    });
  } catch (error) {
    await clientApi(`/uploads/${initiated.id}/abort/`, { method: "POST" }).catch(() => undefined);
    throw error;
  }
}
