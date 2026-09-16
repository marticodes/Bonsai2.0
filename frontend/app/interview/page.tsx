"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import { useState } from "react";

type Importance = "Mildly Preferred" | "Preferred" | "Essential";

type Message = {
  role: "assistant" | "user";
  content: string;
};

const questions = [
  "What would you like your Bluesky feed to help you with?",
  "What topics are most important for you to see?",
  "Are there any topics or types of content you would rather avoid?",
  "What kind of tone or style do you prefer in your feed?",
];

export default function InterviewPage() {
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: questions[0],
    },
  ]);

  const [waitingForImportance, setWaitingForImportance] = useState(false);

  const [importance, setImportance] =
    useState<Importance | null>(null);

    async function submitAnswer() {
        if (!answer.trim()) return;
      
        const userMessage: Message = {
          role: "user",
          content: answer.trim(),
        };
      
        const updatedMessages = [...messages, userMessage];
      
        setMessages(updatedMessages);
        setAnswer("");
        setWaitingForImportance(false);
      
        try {
          const response = await fetch(
            "http://127.0.0.1:8000/api/interview/message",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                conversation: updatedMessages,
              }),
            }
          );
      
          if (!response.ok) {
            throw new Error("Failed to get AI response");
          }
      
          const data = await response.json();
      
          setMessages([
            ...updatedMessages,
            {
              role: "assistant",
              content: data.message,
            },
          ]);
        } catch (error) {
          console.error(error);
        }
      }

    function submitImportance(value: Importance) {
        setImportance(value);
        setWaitingForImportance(false);
    }

  return (
    <main className="min-h-screen bg-gray-50 px-6 py-10">
      <div className="mx-auto flex min-h-[90vh] max-w-3xl flex-col">

        {/* Header */}
        <header className="mb-8">
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="rounded-full bg-black p-2 text-white">
                <Sparkles size={16} />
              </div>

              <span className="font-medium">
                Feed Interview
              </span>
            </div>

            <span className="text-sm text-gray-400">
              Stage {Math.min(questionIndex + 1, 3)} of 3
            </span>
          </div>

          {/* Progress */}
          <div className="h-1.5 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-black transition-all"
              style={{
                width: `${Math.min(
                  ((questionIndex + 1) / 3) * 100,
                  100
                )}%`,
              }}
            />
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 space-y-5 overflow-y-auto pb-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user"
                  ? "justify-end"
                  : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <div className="mr-3 mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-black text-white">
                  <Sparkles size={15} />
                </div>
              )}

              <div
                className={`max-w-xl rounded-2xl px-5 py-3.5 ${
                  message.role === "user"
                    ? "rounded-br-md bg-black text-white"
                    : "rounded-tl-md bg-white text-gray-800 shadow-sm"
                }`}
              >
                {message.content}
              </div>
            </div>
          ))}

          {/* Importance selector */}
          {waitingForImportance && (
            <div className="ml-11 pt-2">
              <p className="mb-3 text-sm text-gray-500">
                How important is this to you?
              </p>

              <div className="flex flex-wrap gap-2">
                {(
                  [
                    "Mildly Preferred",
                    "Preferred",
                    "Essential",
                  ] as Importance[]
                ).map((option) => (
                  <button
                    key={option}
                    onClick={() => submitImportance(option)}
                    className={`rounded-full border px-4 py-2 text-sm transition ${
                      importance === option
                        ? "border-black bg-black text-white"
                        : "border-gray-200 bg-white hover:border-gray-400"
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        {!waitingForImportance && questionIndex < questions.length && (
          <div className="border-t border-gray-200 pt-5">
            <div className="flex items-end gap-3">
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    !e.shiftKey
                  ) {
                    e.preventDefault();
                    submitAnswer();
                  }
                }}
                placeholder="Write your answer..."
                className="min-h-14 flex-1 resize-none rounded-2xl border border-gray-200 bg-white px-4 py-3 outline-none focus:border-gray-400"
              />

              <button
                onClick={submitAnswer}
                disabled={!answer.trim()}
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-black text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-30"
              >
                <ArrowRight size={18} />
              </button>
            </div>

            <p className="mt-2 text-center text-xs text-gray-400">
              Press Enter to continue · Shift + Enter for a new line
            </p>
          </div>
        )}
      </div>
    </main>
  );
}