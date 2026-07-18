"use client";

import { useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

const EXAMPLES = [
  "I've been at my job for 4 years and hate it but I'm scared to quit and freelance. I feel anxious about money.",
  "Should I buy a bike worth 50k or save the money? I really want it but I'm not sure it's practical.",
  "I got into two colleges — one is prestigious but expensive, the other is affordable but less known. I'm confused.",
  "My relationship has been rocky for 2 years. I love my partner but we keep fighting. Should I stay or leave?",
];

export default function ChatPage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [extracted, setExtracted] = useState<any>(null);

  const handleAnalyze = async () => {
    if (text.length < 10) {
      setError("Please describe your decision in more detail.");
      return;
    }

    setLoading(true);
    setError("");
    setExtracted(null);

    try {
      const res = await axios.post("http://localhost:8000/api/chat", { text });
      const { result, extracted_input } = res.data;

      // Show what was extracted briefly
      setExtracted(extracted_input);

      // Store result and navigate
      localStorage.setItem("decidr_result", JSON.stringify(result));
      localStorage.setItem("decidr_web_data", JSON.stringify(res.data.web_data || null));

      // Short delay so user sees what was extracted
      setTimeout(() => {
        window.location.href = "/result";
      }, 2000);

    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
        "Something went wrong. Try the guided form instead."
      );
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between">
        <a href="/" className="text-xl font-bold text-slate-900">DeciDr</a>
        <a href="/analyze">
          <Button variant="outline" size="sm">Use Guided Form Instead</Button>
        </a>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-10 space-y-6">

        {/* Title */}
        <div className="text-center space-y-2">
          <Badge variant="outline" className="text-slate-500">Quick Mode</Badge>
          <h1 className="text-3xl font-bold text-slate-900">
            Just tell us what's on your mind
          </h1>
          <p className="text-slate-500">
            Describe your situation in your own words. DeciDr will understand
            and run the full psychology analysis automatically.
          </p>
        </div>

        {/* Main Input */}
        <Card>
          <CardContent className="p-6 space-y-4">
            <Textarea
              placeholder="e.g. I've been at my job for 4 years and I really hate it. I want to quit and start freelancing but I'm scared about money. My friends say I should stay but I feel like I'm wasting my potential..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="min-h-[180px] text-base resize-none"
              maxLength={2000}
              disabled={loading}
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-400">{text.length}/2000</p>
              <Button
                onClick={handleAnalyze}
                disabled={text.length < 10 || loading}
                className="px-8"
              >
                {loading ? "Analyzing..." : "Analyze →"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-100 rounded-lg p-4 text-sm text-red-600">
            {error}
            <a href="/analyze" className="underline ml-2">Try the guided form →</a>
          </div>
        )}

        {/* Extracted preview */}
        {extracted && (
          <Card className="border-green-100 bg-green-50">
            <CardHeader>
              <CardTitle className="text-base text-green-800">
                ✓ Understood your decision
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-green-700">
              <p><strong>Question:</strong> {extracted.question}</p>
              <p><strong>Category:</strong> {extracted.category}</p>
              <p><strong>Options:</strong> {extracted.options?.map((o: any) => o.name).join(" vs ")}</p>
              <p><strong>Emotional state:</strong> {extracted.emotional_state} ({extracted.emotional_intensity}/10)</p>
              <p className="text-xs text-green-500 mt-2">Redirecting to your analysis...</p>
            </CardContent>
          </Card>
        )}

        {/* Loading state */}
        {loading && !extracted && (
          <Card className="border-blue-100 bg-blue-50">
            <CardContent className="p-6 text-center space-y-3">
              <div className="text-2xl">🧠</div>
              <p className="text-blue-700 font-medium">Understanding your situation...</p>
              <p className="text-blue-500 text-sm">
                DeciDr is extracting the decision structure and running the psychology analysis.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Examples */}
        {!loading && !extracted && (
          <div className="space-y-3">
            <p className="text-xs text-slate-400 uppercase tracking-wide text-center">
              Try an example
            </p>
            {EXAMPLES.map((example, i) => (
              <button
                key={i}
                onClick={() => setText(example)}
                className="w-full text-left text-sm text-slate-600 bg-white border border-slate-100 rounded-lg p-4 hover:border-blue-200 hover:bg-blue-50 transition-colors"
              >
                "{example}"
              </button>
            ))}
          </div>
        )}

        {/* How it works */}
        {!loading && !extracted && (
          <Card className="border-slate-100">
            <CardContent className="p-6">
              <p className="text-sm font-medium text-slate-700 mb-3">How Quick Mode works</p>
              <div className="space-y-2 text-sm text-slate-500">
                <div className="flex gap-3">
                  <span className="text-blue-400 font-bold">1</span>
                  <span>You describe your situation freely in plain text</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-blue-400 font-bold">2</span>
                  <span>DeciDr uses AI to extract the decision structure automatically</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-blue-400 font-bold">3</span>
                  <span>The psychology engine (CPT + Values + Bias detection) runs</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-blue-400 font-bold">4</span>
                  <span>You get a full research-backed recommendation</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

      </div>
    </main>
  );
}
