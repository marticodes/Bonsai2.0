"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import { useState } from "react";

export default function Home() {
  const [answer, setAnswer] = useState("");

  return (
    <main className="min-h-screen bg-gray-50 px-6 py-12">
      <div className="mx-auto flex min-h-[80vh] max-w-3xl flex-col">
        
        {/* Header */}
        <div className="mb-12 text-center">
          <div className="mb-4 flex justify-center">
            <div className="rounded-full bg-black p-3 text-white">
              <Sparkles size={22} />
            </div>
          </div>

          <h1 className="text-4xl font-semibold tracking-tight">
            Build your feed
          </h1>

          <p className="mt-3 text-gray-500">
            Let's figure out what you want to see on Bluesky.
          </p>
        </div>

        {/* Conversation */}
        <div className="flex-1 space-y-6">
          
          {/* Assistant message */}
          <div className="flex items-start gap-3">
            <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-black text-white">
              <Sparkles size={17} />
            </div>

            <div className="max-w-xl rounded-2xl rounded-tl-md bg-white px-5 py-4 shadow-sm">
              <p className="text-gray-800">
                Let's start with the big picture. What would you like
                your Bluesky feed to help you with?
              </p>
            </div>
          </div>

          {/* User input */}
          <div className="ml-12">
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Tell me what you're looking for..."
              className="min-h-32 w-full resize-none rounded-2xl border border-gray-200 bg-white p-4 text-gray-800 outline-none transition focus:border-gray-400 focus:ring-2 focus:ring-gray-100"
            />
          </div>
        </div>

        {/* Continue */}
        <div className="mt-8 flex justify-end">
          <button
            disabled={!answer.trim()}
            className="flex items-center gap-2 rounded-full bg-black px-5 py-3 text-sm font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-30"
          >
            Continue
            <ArrowRight size={17} />
          </button>
        </div>

      </div>
    </main>
  );
}