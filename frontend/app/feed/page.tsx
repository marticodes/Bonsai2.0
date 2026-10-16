"use client";

import { useEffect, useState } from "react";

type Post = {
  uri: string;
  cid: string;
  text: string;
  author: string;
  display_name: string;
  score: number;
  reason: string;
};

export default function FeedPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    generateFeed();
  }, []);

  const generateFeed = async () => {
    try {
      const savedSpecification =
        localStorage.getItem("feedSpecification");

      if (!savedSpecification) {
        setError(
          "No Feed Specification found. Complete the interview first."
        );
        setLoading(false);
        return;
      }

      const specification = JSON.parse(
        savedSpecification
      );

      const response = await fetch(
        "http://127.0.0.1:8000/api/feed/generate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            specification,
            feed_uri:
              "at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.generator/hot-classic",
            limit: 30,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to generate feed");
      }

      const data = await response.json();

      setPosts(data.posts);
    } catch (error) {
      console.error(error);
      setError("Something went wrong while generating the feed.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <main style={{ padding: "40px" }}>
        <h1>Generating your feed...</h1>
        <p>
          Fetching Bluesky posts and ranking them for you.
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main style={{ padding: "40px" }}>
        <h1>Personalized Feed</h1>
        <p>{error}</p>
      </main>
    );
  }

  return (
    <main
      style={{
        maxWidth: "650px",
        margin: "0 auto",
        padding: "40px 20px",
      }}
    >
      <h1>My Feed</h1>

      <p style={{ marginBottom: "30px" }}>
        Posts ranked according to your Feed Specification.
      </p>

      {posts.map((post) => (
        <article
          key={post.uri}
          style={{
            border: "1px solid #ddd",
            borderRadius: "12px",
            padding: "20px",
            marginBottom: "16px",
          }}
        >
          <div style={{ marginBottom: "10px" }}>
            <strong>{post.display_name}</strong>
            <span
              style={{
                marginLeft: "8px",
                color: "#666",
              }}
            >
              @{post.author}
            </span>
          </div>

          <p
            style={{
              whiteSpace: "pre-wrap",
              lineHeight: "1.5",
            }}
          >
            {post.text}
          </p>

          <div
            style={{
              marginTop: "15px",
              paddingTop: "12px",
              borderTop: "1px solid #eee",
              fontSize: "14px",
              color: "#666",
            }}
          >
            <strong>
              Score: {post.score.toFixed(2)}
            </strong>

            <p>{post.reason}</p>
          </div>
        </article>
      ))}
    </main>
  );
}