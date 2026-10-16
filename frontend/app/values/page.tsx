"use client";

import { useEffect, useState } from "react";

type ValueScores = Record<string, number>;

type Post = {
  uri: string;
  cid: string;
  text: string;
  author: string;
  display_name: string;
  values: ValueScores;
};

function sortedValues(values: ValueScores) {
  return Object.entries(values).sort((a, b) => b[1] - a[1]);
}

export default function ValuesPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [selected, setSelected] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadFeed();
  }, []);

  const loadFeed = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/values/feed",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            feed_uri:
              "at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/hot-classic",
            limit: 20,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load values feed");
      }

      const data = await response.json();
      setPosts(data.posts);
    } catch (err) {
      console.error(err);
      setError("Something went wrong while loading the values feed.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <main
        style={{
          minHeight: "100vh",
          background: "#ffffff",
          color: "#111",
          padding: "40px",
        }}
      >
        <h1 style={{ fontSize: "28px", fontWeight: 600 }}>Values</h1>
        <p style={{ marginTop: "12px", color: "#555" }}>
          Fetching Bluesky posts and classifying Schwartz values…
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main
        style={{
          minHeight: "100vh",
          background: "#ffffff",
          color: "#111",
          padding: "40px",
        }}
      >
        <h1 style={{ fontSize: "28px", fontWeight: 600 }}>Values</h1>
        <p style={{ marginTop: "12px" }}>{error}</p>
      </main>
    );
  }

  if (selected) {
    const ranked = sortedValues(selected.values);

    return (
      <main
        style={{
          minHeight: "100vh",
          background: "#ffffff",
          color: "#111",
          maxWidth: "650px",
          margin: "0 auto",
          padding: "40px 20px",
        }}
      >
        <button
          type="button"
          onClick={() => setSelected(null)}
          style={{
            border: "none",
            background: "transparent",
            color: "#555",
            cursor: "pointer",
            padding: 0,
            marginBottom: "24px",
            fontSize: "14px",
          }}
        >
          ← Back to feed
        </button>

        <article>
          <div style={{ marginBottom: "10px" }}>
            <strong>{selected.display_name}</strong>
            <span style={{ marginLeft: "8px", color: "#666" }}>
              @{selected.author}
            </span>
          </div>

          <p
            style={{
              whiteSpace: "pre-wrap",
              lineHeight: 1.5,
              marginBottom: "32px",
            }}
          >
            {selected.text}
          </p>
        </article>

        <section>
          <h2
            style={{
              fontSize: "18px",
              fontWeight: 600,
              marginBottom: "16px",
            }}
          >
            Value profile
          </h2>
          <p
            style={{
              fontSize: "14px",
              color: "#666",
              marginBottom: "20px",
            }}
          >
            All 19 Schwartz Basic Human Values, highest to lowest.
          </p>

          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {ranked.map(([name, score]) => (
              <li
                key={name}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 56px",
                  gap: "12px",
                  alignItems: "center",
                  padding: "10px 0",
                  borderBottom: "1px solid #eee",
                }}
              >
                <div>
                  <div style={{ fontSize: "14px", marginBottom: "6px" }}>
                    {name}
                  </div>
                  <div
                    style={{
                      height: "6px",
                      background: "#f0f0f0",
                      borderRadius: "3px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.round(score * 100)}%`,
                        height: "100%",
                        background: "#111",
                        borderRadius: "3px",
                      }}
                    />
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "13px",
                    color: "#444",
                    textAlign: "right",
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {score.toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </main>
    );
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#ffffff",
        color: "#111",
        maxWidth: "650px",
        margin: "0 auto",
        padding: "40px 20px",
      }}
    >
      <h1 style={{ fontSize: "28px", fontWeight: 600 }}>Values</h1>
      <p style={{ margin: "12px 0 30px", color: "#555" }}>
        Bluesky posts with Schwartz value profiles. Click a post for the
        full 19-dimensional vector.
      </p>

      {posts.map((post) => {
        const top = sortedValues(post.values).slice(0, 3);

        return (
          <article
            key={post.uri}
            role="button"
            tabIndex={0}
            onClick={() => setSelected(post)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setSelected(post);
              }
            }}
            style={{
              borderBottom: "1px solid #eee",
              padding: "20px 0",
              cursor: "pointer",
            }}
          >
            <div style={{ marginBottom: "10px" }}>
              <strong>{post.display_name}</strong>
              <span style={{ marginLeft: "8px", color: "#666" }}>
                @{post.author}
              </span>
            </div>

            <p
              style={{
                whiteSpace: "pre-wrap",
                lineHeight: 1.5,
                marginBottom: "12px",
              }}
            >
              {post.text}
            </p>

            <div style={{ fontSize: "13px", color: "#666" }}>
              {top.map(([name, score], i) => (
                <span key={name}>
                  {i > 0 ? " · " : ""}
                  {name} {score.toFixed(2)}
                </span>
              ))}
            </div>
          </article>
        );
      })}
    </main>
  );
}
