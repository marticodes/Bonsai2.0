"use client";

import { useEffect, useRef, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

type ExtractedFrame = {
  filename: string;
  timestamp_seconds: number;
  image: string;
};

type ClusteredScreenshot = {
  frame_index: number;
  filename: string;
  timestamp_seconds: number;
  ocr_text: string;
  normalized_text: string;
  creator: string;
};

type ScreenshotCluster = {
  cluster_id: number;
  screenshots: ClusteredScreenshot[];
};

type ExtractionResult = {
  duration_seconds: number;
  interval_seconds: number;
  total_frames: number;
  frames: ExtractedFrame[];
  clusters?: ScreenshotCluster[];
  clustering_error?: string;
};

type ClassifiedPost = {
  cluster_id: number;
  category: string;
};

type ThemeCategory = {
  category: string;
  count: number;
  percentage: number;
};

type ThemeSummary = {
  total_posts: number;
  posts: ClassifiedPost[];
  categories: ThemeCategory[];
};

type Analysis = {
    interpretation: string;
    values: {
      value: string;
      type: "explicit" | "inferred";
      direction: string;
      evidence: string;
      confidence: "high" | "medium" | "low";
    }[];
    possible_norms: string[];
    uncertainty: string;
  };

export default function VideoAnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [analyses, setAnalyses] = useState<Record<number, Analysis>>({});
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState<Record<number, boolean>>({});
  const [error, setError] = useState("");
  const [analysisErrors, setAnalysisErrors] = useState<
    Record<number, string>
  >({});
  const [themes, setThemes] = useState<ThemeSummary | null>(null);
  const [classifying, setClassifying] = useState(false);
  const [themeError, setThemeError] = useState("");
  const skipStoredThemes = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function loadStoredThemes() {
      try {
        const response = await fetch(`${API_URL}/api/video/themes`);
        if (!response.ok) return;
        const data: ThemeSummary = await response.json();
        if (!cancelled && !skipStoredThemes.current && data.total_posts > 0) {
          setThemes(data);
        }
      } catch {
        // The dashboard still appears after the next classification.
      }
    }

    loadStoredThemes();
    return () => {
      cancelled = true;
    };
  }, []);

  async function extractScreenshots() {
    if (!file) {
      setError("Please select a video first.");
      return;
    }

    skipStoredThemes.current = true;
    setLoading(true);
    setError("");
    setResult(null);
    setAnalyses({});
    setAnalysisErrors({});
    setThemes(null);
    setThemeError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/api/video/extract-frames`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(
          data?.detail || "Failed to extract screenshots."
        );
      }

      const data: ExtractionResult = await response.json();
      setResult(data);
      if (data.clusters && data.clusters.length > 0) {
        await classifyThemes(data.clusters);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  }

  async function classifyThemes(clusters: ScreenshotCluster[]) {
    setClassifying(true);
    setThemeError("");

    try {
      const response = await fetch(`${API_URL}/api/video/classify-themes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          posts: clusters.map((cluster) => ({
            cluster_id: cluster.cluster_id,
            screenshots: cluster.screenshots.map((shot) => ({
              ocr_text: shot.ocr_text,
              normalized_text: shot.normalized_text,
            })),
          })),
        }),
      });

      const data = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(data?.detail || "Theme classification failed.");
      }

      setThemes(data);
    } catch (err) {
      setThemeError(
        err instanceof Error ? err.message : "Theme classification failed."
      );
    } finally {
      setClassifying(false);
    }
  }

  async function analyzeFrame(
    frame: ExtractedFrame,
    index: number
  ) {
    setAnalyzing((previous) => ({
      ...previous,
      [index]: true,
    }));

    setAnalysisErrors((previous) => ({
      ...previous,
      [index]: "",
    }));

    try {
      const response = await fetch(
        `${API_URL}/api/video/analyze-screenshot`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            image: frame.image,
          }),
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail || "Screenshot analysis failed."
        );
      }

      setAnalyses((previous) => ({
        ...previous,
        [index]: data.analysis,
      }));
    } catch (err) {
      setAnalysisErrors((previous) => ({
        ...previous,
        [index]:
          err instanceof Error
            ? err.message
            : "Screenshot analysis failed.",
      }));
    } finally {
      setAnalyzing((previous) => ({
        ...previous,
        [index]: false,
      }));
    }
  }

  async function analyzeAllFrames() {
    if (!result) return;

    // Process sequentially to avoid sending too many requests at once.
    for (let index = 0; index < result.frames.length; index++) {
      if (analyses[index]) continue;

      await analyzeFrame(result.frames[index], index);
    }
  }

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const selectedFile = event.target.files?.[0] ?? null;

    setFile(selectedFile);
    setResult(null);
    setAnalyses({});
    setAnalysisErrors({});
    setError("");
    setThemeError("");
  }

  function formatTime(seconds: number) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);

    return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
  }

  function renderAnalysis(analysis: Analysis) {
    if (!analysis) {
      return <p style={{ color: "#111827" }}>No analysis available.</p>;
    }
  
    return (
      <div
        style={{
          padding: 16,
          borderTop: "1px solid #ddd",
          lineHeight: 1.5,
          fontSize: 14,
          color: "#111827",
          background: "#ffffff",
        }}
      >
        <h3 style={{ marginBottom: 6 }}>Interpretation</h3>
        <p style={{ marginTop: 0 }}>
          {analysis.interpretation || "No interpretation available."}
        </p>
  
        <h3 style={{ marginBottom: 6 }}>Values identified</h3>
  
        {analysis.values?.length ? (
          analysis.values.map((item, index) => (
            <div
              key={index}
              style={{
                marginBottom: 12,
                paddingBottom: 10,
                borderBottom: "1px solid #eee",
              }}
            >
              <strong>{item.value}</strong>
  
              <p style={{ margin: "4px 0" }}>
                {item.type} · {item.direction} · Confidence: {item.confidence}
              </p>
  
              <p style={{ margin: "4px 0" }}>
                <strong>Evidence:</strong> {item.evidence}
              </p>
            </div>
          ))
        ) : (
          <p>No sufficiently supported values identified.</p>
        )}
  
        <h3 style={{ marginBottom: 6 }}>Possible social norms</h3>
  
        {analysis.possible_norms?.length ? (
          <ul style={{ paddingLeft: 20 }}>
            {analysis.possible_norms.map((norm, index) => (
              <li key={index}>{norm}</li>
            ))}
          </ul>
        ) : (
          <p>No clear social norms identified.</p>
        )}
  
        <h3 style={{ marginBottom: 6 }}>Uncertainty</h3>
        <p style={{ marginTop: 0 }}>
          {analysis.uncertainty || "The interpretation may be incomplete."}
        </p>
      </div>
    );
  }

  function renderFrame(
    frame: ExtractedFrame,
    index: number,
    ocr?: ClusteredScreenshot,
  ) {
    return (
      <article
        key={`${frame.timestamp_seconds}-${index}`}
        style={{
          border: "1px solid #ddd",
          borderRadius: 12,
          overflow: "hidden",
          background: "#fff",
          minWidth: 0,
        }}
      >
        <div style={{ background: "#f3f3f3", padding: 12 }}>
          <strong>Screenshot {index + 1}</strong>
          <p style={{ margin: "4px 0", color: "#666" }}>
            {ocr?.filename || frame.filename}
          </p>
          <p style={{ marginBottom: 0, color: "#666" }}>
            Timestamp: {formatTime(frame.timestamp_seconds)}
          </p>
        </div>

        <img
          src={frame.image}
          alt={`Screenshot at ${frame.timestamp_seconds} seconds`}
          style={{
            display: "block",
            width: "100%",
            height: 320,
            objectFit: "contain",
            background: "#111",
          }}
        />

        {ocr && (
          <div
            style={{
              padding: 12,
              borderTop: "1px solid #eee",
              fontSize: 13,
              lineHeight: 1.5,
              color: "#111827",
            }}
          >
            {ocr.creator && (
              <p style={{ margin: "0 0 10px" }}>
                <strong>Creator:</strong> {ocr.creator}
              </p>
            )}
            <strong>OCR text</strong>
            <p style={{ margin: "4px 0 10px", whiteSpace: "pre-wrap" }}>
              {ocr.ocr_text || "No text detected."}
            </p>
            <strong>Normalized text</strong>
            <p style={{ margin: "4px 0 0" }}>
              {ocr.normalized_text ||
                "No distinctive text left after normalization."}
            </p>
          </div>
        )}

        <div style={{ padding: 12 }}>
          <button
            onClick={() => analyzeFrame(frame, index)}
            disabled={Boolean(analyzing[index])}
            style={buttonStyle(Boolean(analyzing[index]))}
          >
            {analyzing[index]
              ? "Analyzing..."
              : analyses[index]
                ? "Analyze Again"
                : "Analyze Screenshot"}
          </button>

          {analysisErrors[index] && (
            <p style={{ color: "#b42318" }}>
              {analysisErrors[index]}
            </p>
          )}
        </div>

        {analyses[index] && renderAnalysis(analyses[index])}
      </article>
    );
  }

  const screenshotGridStyle = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
    gap: 24,
  } as const;

  return (
    <main
        style={{
            maxWidth: 1100,
            margin: "0 auto",
            padding: "40px 24px",
            color: "#111827",
            background: "#ffffff",
            minHeight: "100vh",
        }}
        >
      <header style={{ marginBottom: 32 }}>
        <p
          style={{
            fontSize: 13,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: 2,
            color: "#777",
          }}
        >
          Bonsai2.0 · Research prototype
        </p>

        <h1 style={{ fontSize: 36, marginBottom: 12 }}>
          Video Analysis
        </h1>

        <p style={{ fontSize: 16, lineHeight: 1.7, color: "#555" }}>
          Upload a social media screen recording. The system extracts
          one screenshot every five seconds, reads the visible text, and
          groups consecutive screenshots that appear to show the same post.
        </p>
      </header>

      <section
        style={{
          padding: 24,
          border: "1px solid #ddd",
          borderRadius: 12,
          marginBottom: 32,
        }}
      >
        <h2>1. Upload a recording</h2>

        <p style={{ color: "#666", lineHeight: 1.6 }}>
          Supported formats: MP4, MOV, AVI, MKV, and WebM.
          Maximum file size: 100 MB.
        </p>

        <input
          type="file"
          accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,video/webm,.mp4,.mov,.avi,.mkv,.webm"
          onChange={handleFileChange}
          style={{
            display: "block",
            marginTop: 20,
            marginBottom: 20,
            maxWidth: "100%",
          }}
        />

        {file && (
          <p>
            Selected: {file.name} (
            {(file.size / (1024 * 1024)).toFixed(2)} MB)
          </p>
        )}

        <button
          onClick={extractScreenshots}
          disabled={!file || loading}
          style={buttonStyle(!file || loading)}
        >
          {loading ? "Extracting and grouping..." : "Extract Screenshots"}
        </button>

        {error && <p style={{ color: "#b42318" }}>{error}</p>}
      </section>

      {!result && (themes || classifying || themeError) && (
        <ThemeDashboard
          themes={themes}
          loading={classifying}
          error={themeError}
        />
      )}

      {result && (
        <section>
          <h2>2. Extracted screenshots</h2>

          <p>
            Duration: {formatTime(result.duration_seconds)} ·
            Interval: {result.interval_seconds} seconds ·
            Screenshots: {result.total_frames}
            {result.clusters && result.clusters.length > 0 && (
              <> · Potential posts: {result.clusters.length}</>
            )}
          </p>

          {result.clustering_error && (
            <p style={{ color: "#b42318" }}>{result.clustering_error}</p>
          )}

          {(classifying || themeError || themes) && (
            <ThemeDashboard
              themes={themes}
              loading={classifying}
              error={themeError}
            />
          )}

          {result.frames.length > 0 && (
            <button
              onClick={analyzeAllFrames}
              disabled={Object.values(analyzing).some(Boolean)}
              style={{
                ...buttonStyle(
                  Object.values(analyzing).some(Boolean)
                ),
                marginBottom: 24,
              }}
            >
              {Object.values(analyzing).some(Boolean)
                ? "Analyzing screenshots..."
                : "Analyze All Screenshots"}
            </button>
          )}

          {result.clusters && result.clusters.length > 0 ? (
            result.clusters.map((cluster) => {
              const first = cluster.screenshots[0];
              const last =
                cluster.screenshots[cluster.screenshots.length - 1];
              const category = themes?.posts.find(
                (post) => post.cluster_id === cluster.cluster_id
              )?.category;

              return (
                <section
                  key={cluster.cluster_id}
                  style={{
                    marginBottom: 32,
                    padding: 16,
                    border: "1px solid #ddd",
                    borderRadius: 12,
                  }}
                >
                  <h3 style={{ marginTop: 0, marginBottom: 6 }}>
                    Potential post {cluster.cluster_id}
                  </h3>
                  <p style={{ marginTop: 0, color: "#555" }}>
                    {cluster.screenshots.length} screenshot
                    {cluster.screenshots.length === 1 ? "" : "s"}
                    {" · "}
                    {formatTime(first.timestamp_seconds)}
                    {last.timestamp_seconds !== first.timestamp_seconds && (
                      <>–{formatTime(last.timestamp_seconds)}</>
                    )}
                    {first.creator && <> · {first.creator}</>}
                    {category && <> · {category}</>}
                  </p>
                  <div style={screenshotGridStyle}>
                    {cluster.screenshots.map((shot) =>
                      renderFrame(
                        result.frames[shot.frame_index],
                        shot.frame_index,
                        shot,
                      ),
                    )}
                  </div>
                </section>
              );
            })
          ) : (
            <div style={screenshotGridStyle}>
              {result.frames.map((frame, index) =>
                renderFrame(frame, index),
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}

const CATEGORY_COLORS: Record<string, string> = {
  Beauty: "#e85d8c",
  Gaming: "#7c5cbf",
  Sports: "#2f9e6b",
  Entertainment: "#e09a2b",
  Lifestyle: "#3d8bfd",
  Education: "#2a6fdb",
  Technology: "#3a3a3a",
  Relationships: "#d4537e",
  News: "#c4492c",
  Other: "#8a8f98",
};

function ThemeDashboard({
  themes,
  loading,
  error,
}: {
  themes: ThemeSummary | null;
  loading: boolean;
  error: string;
}) {
  const slices = themes ? pieSlices(themes.categories) : [];

  return (
    <section
      style={{
        padding: 24,
        border: "1px solid #ddd",
        borderRadius: 12,
        marginBottom: 32,
      }}
    >
      <h2 style={{ marginTop: 0 }}>Theme dashboard</h2>
      <p style={{ color: "#555", marginTop: 0 }}>
        One primary category per unique post, classified from the OCR text
        already grouped for that post.
      </p>

      {loading && <p>Classifying themes from OCR text...</p>}
      {error && <p style={{ color: "#b42318" }}>{error}</p>}

      {themes && (
        <>
          <p style={{ fontSize: 18 }}>
            <strong>Total analysed posts:</strong> {themes.total_posts}
          </p>
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 32,
              alignItems: "center",
            }}
          >
            <PieChart slices={slices} />
            <ul
              style={{
                listStyle: "none",
                padding: 0,
                margin: 0,
                minWidth: 260,
                flex: 1,
              }}
            >
              {themes.categories.map((item) => (
                <li
                  key={item.category}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 16,
                    padding: "6px 0",
                    borderBottom: "1px solid #eee",
                  }}
                >
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span
                      style={{
                        width: 12,
                        height: 12,
                        borderRadius: 2,
                        background: CATEGORY_COLORS[item.category] || "#8a8f98",
                        display: "inline-block",
                      }}
                    />
                    {item.category}
                  </span>
                  <span>
                    {item.percentage.toFixed(1)}% · {item.count}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  );
}

function pieSlices(categories: ThemeCategory[]) {
  const active = categories.filter((item) => item.count > 0);
  const total = active.reduce((sum, item) => sum + item.count, 0);
  let angle = -Math.PI / 2;

  return active.map((item) => {
    const sweep = total === 0 ? 0 : (item.count / total) * Math.PI * 2;
    const start = angle;
    const end = angle + sweep;
    angle = end;
    return { ...item, start, end };
  });
}

function PieChart({
  slices,
}: {
  slices: Array<ThemeCategory & { start: number; end: number }>;
}) {
  const size = 220;
  const center = size / 2;
  const radius = 96;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label="Posts by theme"
    >
      {slices.length === 0 ? (
        <circle cx={center} cy={center} r={radius} fill="#eee" />
      ) : (
        slices.map((slice) => (
          <path
            key={slice.category}
            d={slicePath(center, center, radius, slice.start, slice.end)}
            fill={CATEGORY_COLORS[slice.category] || "#8a8f98"}
          >
            <title>
              {slice.category}: {slice.percentage.toFixed(1)}%
            </title>
          </path>
        ))
      )}
    </svg>
  );
}

function slicePath(
  cx: number,
  cy: number,
  radius: number,
  start: number,
  end: number
) {
  if (end - start >= Math.PI * 2 - 0.0001) {
    return `M ${cx} ${cy - radius} A ${radius} ${radius} 0 1 1 ${cx - 0.01} ${cy - radius} Z`;
  }

  const x1 = cx + radius * Math.cos(start);
  const y1 = cy + radius * Math.sin(start);
  const x2 = cx + radius * Math.cos(end);
  const y2 = cy + radius * Math.sin(end);
  const large = end - start > Math.PI ? 1 : 0;
  return `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${large} 1 ${x2} ${y2} Z`;
}

function buttonStyle(disabled: boolean) {
  return {
    padding: "12px 18px",
    background: disabled ? "#aaa" : "#222",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: disabled ? "not-allowed" : "pointer",
    fontSize: 14,
  } as const;
}