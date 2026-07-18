"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

interface OptionScore {
  name: string;
  raw_score: number;
  psychological_value: number;
  values_alignment: number;
  final_score: number;
  breakdown: {
    cpt_framing: string;
    strongest_value: string;
    weakest_value: string;
    bias_adjustment: number;
  };
}

interface BiasFound {
  name: string;
  severity: string;
  description: string;
  how_it_affects_this_decision: string;
  source_paper: string;
}

interface DecisionResult {
  decision_id: string;
  question: string;
  recommendation: string;
  confidence: string;
  biases_detected: BiasFound[];
  option_scores: OptionScore[];
  premortem: string;
  second_order_effects: string;
  narrative: string;
  emotional_state_warning: string | null;
  research_citations: string[];
}

interface WebOptionData {
  financial_security: number;
  personal_growth: number;
  relationships: number;
  autonomy: number;
  stability: number;
  achievement: number;
  wellbeing: number;
  stress_level: number;
  data_summary: string;
}

interface WebData {
  options: Record<string, WebOptionData>;
  search_confidence: string;
  data_sources_used: string[];
}

const severityColor = (s: string) => {
  if (s === "high") return "bg-red-100 text-red-700 border-red-200";
  if (s === "medium") return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-slate-100 text-slate-600 border-slate-200";
};

const confidenceColor = (c: string) => {
  if (c === "high") return "text-green-600";
  if (c === "medium") return "text-amber-600";
  return "text-red-500";
};

const framingColor = (f: string) =>
  f === "GAIN" ? "text-green-600" : "text-red-500";

const goHome = () => {
  localStorage.removeItem("decidr_result");
  localStorage.removeItem("decidr_web_data");
  window.location.href = "/";
};

export default function ResultPage() {
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [webData, setWebData] = useState<WebData | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("decidr_result");
    const storedWeb = localStorage.getItem("decidr_web_data");

    if (!stored) {
      window.location.href = "/";
      return;
    }
    try {
      setResult(JSON.parse(stored));
      if (storedWeb && storedWeb !== "null") {
        setWebData(JSON.parse(storedWeb));
      }
    } catch {
      window.location.href = "/";
    }
  }, []);

  if (!result) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <p className="text-slate-400">Loading your analysis...</p>
      </div>
    );
  }

  const maxScore = 10;

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between">
        <a href="/" className="text-xl font-bold text-slate-900">DeciDr</a>
        <Button variant="outline" size="sm" onClick={goHome}>
          New Analysis
        </Button>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10 space-y-6">

        {/* Question */}
        <div>
          <p className="text-sm text-slate-400 mb-1">Your decision</p>
          <h1 className="text-2xl font-bold text-slate-900">{result.question}</h1>
        </div>

        {/* Recommendation */}
        <Card className="border-blue-100 bg-blue-50">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-blue-500 font-medium mb-1">DeciDr Recommends</p>
                <h2 className="text-3xl font-bold text-slate-900">{result.recommendation}</h2>
                <p className={`text-sm font-medium mt-2 ${confidenceColor(result.confidence)}`}>
                  {result.confidence.toUpperCase()} confidence
                </p>
              </div>
              <div className="text-5xl">🎯</div>
            </div>
          </CardContent>
        </Card>

        {/* Emotional Warning */}
        {result.emotional_state_warning && (
          <Card className="border-amber-100 bg-amber-50">
            <CardContent className="p-4">
              <p className="text-sm text-amber-700">{result.emotional_state_warning}</p>
            </CardContent>
          </Card>
        )}

        {/* ── WEB DATA TRANSPARENCY CARD ── */}
        {webData && (
          <Card className="border-indigo-100 bg-indigo-50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base text-indigo-900">
                  🌐 Real-World Data Used
                </CardTitle>
                <Badge
                  variant="outline"
                  className={`text-xs ${
                    webData.search_confidence === "high"
                      ? "border-green-300 text-green-700"
                      : webData.search_confidence === "medium"
                      ? "border-amber-300 text-amber-700"
                      : "border-red-300 text-red-700"
                  }`}
                >
                  {webData.search_confidence} confidence
                </Badge>
              </div>
              <p className="text-xs text-indigo-500 mt-1">
                Option ratings were auto-populated from web data, not manual estimates.
                {webData.data_sources_used?.length > 0 && (
                  <span> Sources: {webData.data_sources_used.join(", ")}</span>
                )}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(webData.options).map(([optName, data]) => (
                <div key={optName} className="bg-white rounded-lg p-4 border border-indigo-100">
                  <p className="font-semibold text-slate-900 mb-2">{optName}</p>
                  <p className="text-xs text-slate-500 mb-3 leading-relaxed">
                    {data.data_summary}
                  </p>
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    {[
                      { label: "Financial", value: data.financial_security },
                      { label: "Growth", value: data.personal_growth },
                      { label: "Wellbeing", value: data.wellbeing },
                      { label: "Stability", value: data.stability },
                      { label: "Achievement", value: data.achievement },
                      { label: "Autonomy", value: data.autonomy },
                      { label: "Relations", value: data.relationships },
                      { label: "Stress", value: data.stress_level },
                    ].map(({ label, value }) => (
                      <div key={label} className="text-center">
                        <p className="text-slate-400">{label}</p>
                        <p className={`font-bold ${
                          label === "Stress"
                            ? value >= 7 ? "text-red-500" : "text-green-600"
                            : value >= 7 ? "text-green-600" : value >= 5 ? "text-amber-600" : "text-red-500"
                        }`}>
                          {value}/10
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              <p className="text-xs text-indigo-400 italic">
                ⚠ These ratings are generated from web search results and may not reflect your specific situation.
                Use the Guided Form to override any values manually.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Option Scores */}
        <Card>
          <CardHeader>
            <CardTitle>Option Scores</CardTitle>
            <p className="text-sm text-slate-500">
              Combined from CPT psychological value + Schwartz values alignment + bias adjustment
              {webData && " — using real web data"}
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {result.option_scores.map((opt, idx) => (
              <div key={opt.name} className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900">{opt.name}</span>
                    {idx === 0 && (
                      <Badge className="bg-blue-600 text-white text-xs">Recommended</Badge>
                    )}
                    {webData && webData.options[opt.name] && (
                      <Badge variant="outline" className="text-xs border-indigo-200 text-indigo-500">
                        🌐 web data
                      </Badge>
                    )}
                  </div>
                  <span className="text-lg font-bold text-slate-900">
                    {opt.final_score.toFixed(2)}/10
                  </span>
                </div>
                <Progress value={(opt.final_score / maxScore) * 100} className="h-2" />
                <div className="grid grid-cols-3 gap-3 text-sm">
                  <div className="bg-slate-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-400 mb-1">Psych Value</p>
                    <p className="font-semibold text-slate-900">{opt.psychological_value.toFixed(1)}/10</p>
                    <p className={`text-xs mt-1 ${framingColor(opt.breakdown.cpt_framing)}`}>
                      {opt.breakdown.cpt_framing}
                    </p>
                  </div>
                  <div className="bg-slate-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-400 mb-1">Values Fit</p>
                    <p className="font-semibold text-slate-900">{opt.values_alignment.toFixed(1)}/10</p>
                    <p className="text-xs text-slate-400 mt-1 capitalize">
                      ↑ {opt.breakdown.strongest_value.replace(/_/g, " ")}
                    </p>
                  </div>
                  <div className="bg-slate-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-slate-400 mb-1">Bias Adj.</p>
                    <p className={`font-semibold ${opt.breakdown.bias_adjustment < 0 ? "text-red-500" : "text-green-600"}`}>
                      {opt.breakdown.bias_adjustment.toFixed(2)}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">correction</p>
                  </div>
                </div>
                {idx < result.option_scores.length - 1 && <Separator />}
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Biases */}
        {result.biases_detected.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Cognitive Biases Detected</CardTitle>
              <p className="text-sm text-slate-500">
                These psychological patterns may be distorting your judgment.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {result.biases_detected.map((bias) => (
                <div key={bias.name} className="border border-slate-100 rounded-lg p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-900">{bias.name}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${severityColor(bias.severity)}`}>
                      {bias.severity}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600">{bias.how_it_affects_this_decision}</p>
                  <p className="text-xs text-slate-400 italic">{bias.source_paper}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Narrative */}
        <Card>
          <CardHeader><CardTitle>Analysis Narrative</CardTitle></CardHeader>
          <CardContent>
            <div className="text-slate-700 leading-relaxed whitespace-pre-line text-sm">
              {result.narrative}
            </div>
          </CardContent>
        </Card>

        {/* Pre-mortem */}
        <Card>
          <CardHeader>
            <CardTitle>🔮 Pre-Mortem Analysis</CardTitle>
            <p className="text-sm text-slate-500">Klein (2007) — Imagine the decision failed. What went wrong?</p>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-700 leading-relaxed">{result.premortem}</p>
          </CardContent>
        </Card>

        {/* Second Order */}
        <Card>
          <CardHeader>
            <CardTitle>⚡ Second-Order Effects</CardTitle>
            <p className="text-sm text-slate-500">What happens AFTER you make this decision?</p>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-slate-700 leading-relaxed">{result.second_order_effects}</p>
          </CardContent>
        </Card>

        {/* Citations */}
        <Card>
          <CardHeader>
            <CardTitle>📚 Research Citations</CardTitle>
            <p className="text-sm text-slate-500">Every recommendation is grounded in peer-reviewed research.</p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {[...new Set(result.research_citations)].map((cite, i) => (
                <li key={i} className="text-xs text-slate-500 flex gap-2">
                  <span className="text-blue-400 font-medium shrink-0">[{i + 1}]</span>
                  <span>{cite}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* Bottom CTA */}
        <div className="text-center pb-10">
          <p className="text-xs text-slate-300 mb-4">Decision ID: {result.decision_id}</p>
          <Button className="mt-2" onClick={goHome}>
            Analyze Another Decision
          </Button>
        </div>

      </div>
    </main>
  );
}
