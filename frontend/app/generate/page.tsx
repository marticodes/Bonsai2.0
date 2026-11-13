"use client";

import { Download, ImagePlus, LoaderCircle, Sparkles, X } from "lucide-react";
import { useRef, useState } from "react";

type Platform = "snapchat" | "instagram" | "tiktok";
type Format = "text" | "image" | "video";

type GenerateResult = {
  platform: Platform;
  format: Format;
  username: string;
  display_name: string;
  age: number | null;
  caption: string;
  media_mime: string | null;
  media_base64: string | null;
  download: {
    filename: string;
    mime: string;
    base64: string;
  };
};

const API = "http://127.0.0.1:8000/api/generate";
const MAX_SHOTS = 4;

type ReferenceShot = {
  id: string;
  name: string;
  dataUrl: string;
};

async function compressImage(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file);
  const maxEdge = 1280;
  const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    bitmap.close();
    throw new Error("Couldn't read that image. Use a PNG or JPEG.");
  }
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  return canvas.toDataURL("image/jpeg", 0.82);
}

function downloadBase64(filename: string, mime: string, b64: string) {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const blob = new Blob([bytes], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function GeneratePage() {
  const [platform, setPlatform] = useState<Platform>("instagram");
  const [format, setFormat] = useState<Format>("text");
  const [topic, setTopic] = useState("");
  const [tone, setTone] = useState("");
  const [context, setContext] = useState("");
  const [values, setValues] = useState("");
  const [constraints, setConstraints] = useState("");
  const [shots, setShots] = useState<ReferenceShot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<GenerateResult | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  async function onGenerate() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform,
          format,
          topic,
          tone,
          context,
          values,
          constraints,
          reference_images: shots.map((shot) => shot.dataUrl),
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        const detail = data.detail;
        const message =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ")
              : "Generation failed";
        throw new Error(message || "Generation failed");
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function addShots(files: FileList | File[]) {
    const incoming = Array.from(files).filter((file) =>
      file.type.startsWith("image/")
    );
    if (!incoming.length) {
      setError("Upload a PNG or JPEG screenshot.");
      return;
    }

    const room = MAX_SHOTS - shots.length;
    if (room <= 0) {
      setError(`You can attach up to ${MAX_SHOTS} screenshots.`);
      return;
    }

    setError("");
    const accepted = incoming.slice(0, room);
    try {
      const next = await Promise.all(
        accepted.map(async (file) => ({
          id: `${file.name}-${file.lastModified}-${crypto.randomUUID()}`,
          name: file.name,
          dataUrl: await compressImage(file),
        }))
      );
      setShots((current) => [...current, ...next].slice(0, MAX_SHOTS));
      if (incoming.length > room) {
        setError(`Only the first ${MAX_SHOTS} screenshots were kept.`);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't read that image."
      );
    }
  }

  const hasBrief =
    topic.trim() && tone.trim() && context.trim() && values.trim();
  const canSubmit = (hasBrief || shots.length > 0) && !loading;

  return (
    <main className="min-h-screen bg-gray-50 px-6 py-12 text-gray-900">
      <div className="mx-auto grid max-w-5xl gap-10 lg:grid-cols-2">
        <section>
          <div className="mb-8 flex items-center gap-3">
            <div className="rounded-full bg-black p-2.5 text-white">
              <Sparkles size={18} />
            </div>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">
                Synthetic post generator
              </h1>
              <p className="text-sm text-gray-500">
                One fictional post per request for ages 10–16 research.
              </p>
            </div>
          </div>

          <div className="space-y-4 rounded-2xl bg-white p-6 shadow-sm">
            <label className="block text-sm">
              <span className="mb-1.5 block font-medium">Platform</span>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value as Platform)}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 outline-none focus:border-gray-400"
              >
                <option value="snapchat">Snapchat</option>
                <option value="instagram">Instagram</option>
                <option value="tiktok">TikTok</option>
              </select>
            </label>

            <label className="block text-sm">
              <span className="mb-1.5 block font-medium">Format</span>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value as Format)}
                className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 outline-none focus:border-gray-400"
              >
                <option value="text">Text</option>
                <option value="image">Image</option>
                <option value="video">Video (~10s)</option>
              </select>
            </label>

            <div className="text-sm">
              <span className="mb-1.5 block font-medium">
                Reference screenshots{" "}
                <span className="font-normal text-gray-400">
                  {shots.length ? "(style only)" : "(optional)"}
                </span>
              </span>
              <button
                type="button"
                onClick={() => fileInput.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (e.dataTransfer.files.length) {
                    void addShots(e.dataTransfer.files);
                  }
                }}
                className="flex w-full flex-col items-center gap-2 rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-5 text-gray-500 transition hover:border-gray-400 hover:bg-gray-100"
              >
                <ImagePlus size={18} />
                <span>Drop post screenshots, or click to upload</span>
                <span className="text-xs text-gray-400">
                  Up to {MAX_SHOTS} images. The new post matches the vibe
                  without copying names, faces, or the exact caption.
                </span>
              </button>
              <input
                ref={fileInput}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.length) void addShots(e.target.files);
                  e.target.value = "";
                }}
              />
              {shots.length > 0 && (
                <ul className="mt-3 grid grid-cols-4 gap-2">
                  {shots.map((shot) => (
                    <li key={shot.id} className="relative">
                      <img
                        src={shot.dataUrl}
                        alt={shot.name}
                        className="h-20 w-full rounded-lg object-cover"
                      />
                      <button
                        type="button"
                        aria-label={`Remove ${shot.name}`}
                        onClick={() =>
                          setShots((current) =>
                            current.filter((item) => item.id !== shot.id)
                          )
                        }
                        className="absolute right-1 top-1 rounded-full bg-black/70 p-1 text-white"
                      >
                        <X size={12} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {(
              [
                ["Topic", topic, setTopic, "e.g. school lunch drama"],
                ["Tone", tone, setTone, "e.g. sarcastic, anxious, hype"],
                [
                  "Context",
                  context,
                  setContext,
                  "e.g. after tryouts, weekend sleepover",
                ],
                [
                  "Values",
                  values,
                  setValues,
                  "e.g. belonging, honesty, status",
                ],
              ] as const
            ).map(([label, value, setter, placeholder]) => (
              <label key={label} className="block text-sm">
                <span className="mb-1.5 block font-medium">
                  {label}{" "}
                  {shots.length > 0 && (
                    <span className="font-normal text-gray-400">
                      (optional)
                    </span>
                  )}
                </span>
                <input
                  value={value}
                  onChange={(e) => setter(e.target.value)}
                  placeholder={placeholder}
                  className="w-full rounded-xl border border-gray-200 bg-white px-3 py-2.5 outline-none focus:border-gray-400"
                />
              </label>
            ))}

            <label className="block text-sm">
              <span className="mb-1.5 block font-medium">
                Constraints{" "}
                <span className="font-normal text-gray-400">(optional)</span>
              </span>
              <textarea
                value={constraints}
                onChange={(e) => setConstraints(e.target.value)}
                placeholder="e.g. no swearing; include FOMO lightly"
                className="min-h-20 w-full resize-none rounded-xl border border-gray-200 bg-white px-3 py-2.5 outline-none focus:border-gray-400"
              />
            </label>

            <button
              type="button"
              disabled={!canSubmit}
              onClick={onGenerate}
              className="flex w-full items-center justify-center gap-2 rounded-full bg-black px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-30"
            >
              {loading ? (
                <>
                  <LoaderCircle size={17} className="animate-spin" />
                  Generating…
                </>
              ) : (
                shots.length
                  ? "Generate a post similar to this"
                  : "Generate post"
              )}
            </button>

            {error && (
              <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </p>
            )}
          </div>
        </section>

        <section className="rounded-2xl bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wide text-gray-400">
            Preview
          </h2>

          {!result && !loading && (
            <p className="text-sm text-gray-400">
              Generated post will appear here.
            </p>
          )}

          {loading && (
            <p className="text-sm text-gray-500">
              {shots.length
                ? "Reading the screenshot and writing a similar post"
                : "Calling GPT"}
              {format === "image"
                ? " + image API"
                : format === "video"
                  ? " + video API"
                  : ""}
              …
            </p>
          )}

          {result && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
                <div className="mb-3 flex items-center gap-2 text-sm">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-800 text-xs font-semibold text-white">
                    {result.display_name.slice(0, 1)}
                  </div>
                  <div>
                    <div className="font-medium">{result.display_name}</div>
                    <div className="text-xs text-gray-500">
                      @{result.username}
                      {result.age != null ? ` · ${result.age}` : ""} ·{" "}
                      {result.platform}
                    </div>
                  </div>
                </div>

                {result.media_base64 && result.media_mime?.startsWith("image/") && (
                  <img
                    src={`data:${result.media_mime};base64,${result.media_base64}`}
                    alt="Generated synthetic post media"
                    className="mb-3 max-h-[420px] w-full rounded-xl object-cover"
                  />
                )}

                {result.media_base64 && result.media_mime?.startsWith("video/") && (
                  <video
                    controls
                    className="mb-3 max-h-[420px] w-full rounded-xl bg-black"
                    src={`data:${result.media_mime};base64,${result.media_base64}`}
                  />
                )}

                <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-gray-800">
                  {result.caption}
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  downloadBase64(
                    result.download.filename,
                    result.download.mime,
                    result.download.base64
                  )
                }
                className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium transition hover:bg-gray-50"
              >
                <Download size={16} />
                Download {result.download.filename}
              </button>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
