"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import { useState } from "react";

type Message = {
  role: "assistant" | "user";
  content: string;
};

type FeedSpecification = {
  overarching_point: string;
  best_types_of_post: string[];
  desirable_and_decent: string[];
  acceptable: string[];
  better_than_nothing: string[];
  avoid: string[];
  penalize_for: string[];
};


export default function InterviewPage() {
  const [answer, setAnswer] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "What would you like your Bluesky feed to help you with?",
    },
  ]);

  const [stage, setStage] = useState(1);
  const [stageQuestionCount, setStageQuestionCount] = useState(0);
  const [specification, setSpecification] =
    useState<FeedSpecification | null>(null);
  const [generatingSpec, setGeneratingSpec] = useState(false);

  const [waitingForImportance, setWaitingForImportance] = useState(false);

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
                stage: stage,
                stage_question_count: stageQuestionCount,
              }),
            }
          );
      
          if (!response.ok) {
            throw new Error("Failed to get AI response");
          }
      
          const data = await response.json();

          setStage(data.stage);

          setStageQuestionCount(
            data.stage_question_count
          );

          const newMessages = [
            ...updatedMessages,
            {
              role: "assistant" as const,
              content: data.message,
            },
          ];

          setMessages(newMessages);

          if (data.stage === 4 && data.stage_complete) {
            setGeneratingSpec(true);
            const spec = await generateSpecification(newMessages);
            if (spec) {
              setSpecification(spec);
              setStage(5);
            }
            setGeneratingSpec(false);
          }
        } catch (error) {
          console.error(error);
        }
      }

      const generateSpecification = async (
        conversation: Message[]
      ) => {
        try {
          const response = await fetch(
            "http://127.0.0.1:8000/api/interview/specification",
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                conversation,
              }),
            }
          );
      
          if (!response.ok) {
            throw new Error("Failed to generate specification");
          }
      
          const specification = await response.json();
      
          console.log(
            "Generated Feed Specification:",
            specification
          );
      
          return specification;
      
        } catch (error) {
          console.error(
            "Error generating specification:",
            error
          );
      
          return null;
        }
      };

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
              Stage {stage} of 5
            </span>
          </div>

          {/* Progress */}
          <div className="h-1.5 overflow-hidden rounded-full bg-gray-200">
            <div
              className="h-full rounded-full bg-black transition-all"
              style={{
                width: `${Math.min((stage / 5) * 100, 100)}%`,
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
                  ]
                ).map((option) => (
                  <button
                    key={option}
                    onClick={submitAnswer}
                    className="rounded-full border px-4 py-2 text-sm transition border-gray-200 bg-white hover:border-gray-400"
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {generatingSpec && (
          <p className="mb-6 text-center text-sm text-gray-500">
            Generating your feed specification...
          </p>
        )}

        {specification && (
          <section className="mb-8 space-y-5 rounded-2xl bg-white p-6 shadow-sm">
            <h2 className="text-lg font-medium">Feed specification</h2>
            <p className="text-gray-800">{specification.overarching_point}</p>
            {(
              [
                ["Best types of post", specification.best_types_of_post],
                ["Desirable and decent", specification.desirable_and_decent],
                ["Acceptable", specification.acceptable],
                ["Better than nothing", specification.better_than_nothing],
                ["Avoid", specification.avoid],
                ["Penalize for", specification.penalize_for],
              ] as const
            ).map(([title, items]) => (
              <div key={title}>
                <h3 className="mb-2 text-sm font-medium text-gray-500">
                  {title}
                </h3>
                <ul className="list-disc space-y-1 pl-5 text-gray-800">
                  {items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </section>
        )}

        {/* Input */}
        {!waitingForImportance && !specification && !generatingSpec && (
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