import React, { useState } from "react";
import { Zap, Copy, ThumbsUp, Share2 } from "lucide-react";

interface GeneratedContent {
  id: string;
  content_type: string;
  generated_content: string;
  platform?: string;
  seo_score: number;
  engagement_score: number;
}

interface ContentVariant {
  id: string;
  style: string;
  variant_text: string;
}

const ContentGenerator: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"single" | "bulk" | "history">("single");
  const [contentType, setContentType] = useState("product_title");
  const [platform, setPlatform] = useState("amazon");
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [variants, setVariants] = useState<ContentVariant[]>([]);
  const [showVariants, setShowVariants] = useState(false);

  const handleGenerate = () => {
    // Stub: Simulates AI generation
    const stub: GeneratedContent = {
      id: Math.random().toString(36).substr(2, 9),
      content_type: contentType,
      generated_content: `AI-Generated ${contentType} optimized for ${platform} with SEO best practices and engagement hooks.`,
      platform: platform,
      seo_score: 85.5 + Math.random() * 10,
      engagement_score: 78.3 + Math.random() * 15,
    };
    setGeneratedContent(stub);

    // Generate 3 variants
    const variantStyles = ["formal", "casual", "urgent"];
    const newVariants = variantStyles.map((style, idx) => ({
      id: Math.random().toString(36).substr(2, 9),
      style: style,
      variant_text: `${style.charAt(0).toUpperCase() + style.slice(1)} version: ${stub.generated_content}`,
    }));
    setVariants(newVariants);
  };

  return (
    <div className="w-full bg-gradient-to-b from-slate-900 to-slate-800 text-white p-6 rounded-lg">
      <div className="flex items-center mb-6">
        <Zap className="w-6 h-6 text-yellow-400 mr-3" />
        <h1 className="text-3xl font-bold">AI Content Generator (Phase 51)</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-700">
        <button
          onClick={() => setActiveTab("single")}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === "single" ? "border-b-2 border-yellow-500 text-yellow-400" : "text-slate-400"
          }`}
        >
          Single Generation
        </button>
        <button
          onClick={() => setActiveTab("bulk")}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === "bulk" ? "border-b-2 border-yellow-500 text-yellow-400" : "text-slate-400"
          }`}
        >
          Bulk Generation
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`px-4 py-2 font-semibold transition ${
            activeTab === "history" ? "border-b-2 border-yellow-500 text-yellow-400" : "text-slate-400"
          }`}
        >
          History
        </button>
      </div>

      {/* Single Generation Tab */}
      {activeTab === "single" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Content Type</label>
              <select
                value={contentType}
                onChange={(e) => setContentType(e.target.value)}
                className="w-full bg-slate-700 text-white p-2 rounded text-sm"
              >
                <option value="product_title">Product Title</option>
                <option value="product_description">Product Description</option>
                <option value="social_post">Social Post</option>
                <option value="email_subject">Email Subject</option>
                <option value="email_body">Email Body</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2">Platform</label>
              <select
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
                className="w-full bg-slate-700 text-white p-2 rounded text-sm"
              >
                <option value="amazon">Amazon</option>
                <option value="mercado_libre">Mercado Libre</option>
                <option value="instagram">Instagram</option>
                <option value="tiktok">TikTok</option>
                <option value="shopify">Shopify</option>
              </select>
            </div>
          </div>

          <div className="bg-slate-700 p-4 rounded-lg">
            <label className="block text-sm font-semibold mb-2">Original Content (Optional)</label>
            <textarea
              placeholder="Paste existing product description or content..."
              className="w-full bg-slate-600 text-white p-3 rounded text-sm h-24"
            />
          </div>

          <button
            onClick={handleGenerate}
            className="w-full bg-yellow-600 hover:bg-yellow-700 px-6 py-3 rounded font-bold text-lg transition"
          >
            Generate Content
          </button>

          {/* Generated Content Display */}
          {generatedContent && (
            <div className="space-y-4">
              <div className="bg-slate-700 p-4 rounded-lg border border-yellow-500/30">
                <h3 className="font-bold mb-2 text-lg">Generated Content</h3>
                <p className="text-white mb-4">{generatedContent.generated_content}</p>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-slate-600 p-3 rounded">
                    <p className="text-xs text-slate-400">SEO Score</p>
                    <p className="text-2xl font-bold text-green-400">{generatedContent.seo_score.toFixed(1)}</p>
                  </div>
                  <div className="bg-slate-600 p-3 rounded">
                    <p className="text-xs text-slate-400">Engagement Score</p>
                    <p className="text-2xl font-bold text-blue-400">{generatedContent.engagement_score.toFixed(1)}</p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button className="flex-1 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-semibold flex items-center justify-center gap-2">
                    <Copy className="w-4 h-4" /> Copy
                  </button>
                  <button className="flex-1 bg-green-600 hover:bg-green-700 px-4 py-2 rounded font-semibold flex items-center justify-center gap-2">
                    <ThumbsUp className="w-4 h-4" /> Approve
                  </button>
                  <button className="flex-1 bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded font-semibold flex items-center justify-center gap-2">
                    <Share2 className="w-4 h-4" /> Publish
                  </button>
                </div>
              </div>

              {/* Variants */}
              <div className="bg-slate-700 p-4 rounded-lg">
                <button
                  onClick={() => setShowVariants(!showVariants)}
                  className="font-bold mb-3 text-left w-full p-2 hover:bg-slate-600 rounded transition"
                >
                  {showVariants ? "▼" : "▶"} Content Variants ({variants.length})
                </button>

                {showVariants && (
                  <div className="space-y-3">
                    {variants.map((variant) => (
                      <div key={variant.id} className="bg-slate-600 p-3 rounded">
                        <p className="font-semibold capitalize text-sm mb-2">{variant.style}</p>
                        <p className="text-sm text-slate-200 mb-2">{variant.variant_text}</p>
                        <div className="flex gap-2">
                          <button className="flex-1 bg-slate-500 hover:bg-slate-400 px-2 py-1 rounded text-xs font-semibold">
                            Select
                          </button>
                          <button className="flex-1 bg-slate-500 hover:bg-slate-400 px-2 py-1 rounded text-xs font-semibold">
                            Copy
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bulk Generation Tab */}
      {activeTab === "bulk" && (
        <div className="space-y-4">
          <div className="bg-slate-700 p-4 rounded-lg">
            <label className="block text-sm font-semibold mb-2">Batch Name</label>
            <input
              type="text"
              placeholder="e.g., Summer Collection 2024"
              className="w-full bg-slate-600 text-white p-2 rounded text-sm mb-4"
            />

            <label className="block text-sm font-semibold mb-2">Content Type</label>
            <select className="w-full bg-slate-600 text-white p-2 rounded text-sm mb-4">
              <option>product_title</option>
              <option>product_description</option>
              <option>social_post</option>
            </select>

            <label className="block text-sm font-semibold mb-2">Platform</label>
            <select className="w-full bg-slate-600 text-white p-2 rounded text-sm mb-4">
              <option>amazon</option>
              <option>mercado_libre</option>
              <option>all_platforms</option>
            </select>

            <label className="block text-sm font-semibold mb-2">Number of Products</label>
            <input
              type="number"
              placeholder="100"
              className="w-full bg-slate-600 text-white p-2 rounded text-sm mb-4"
            />

            <button className="w-full bg-yellow-600 hover:bg-yellow-700 px-6 py-3 rounded font-bold transition">
              Start Bulk Generation
            </button>
          </div>

          <div className="bg-slate-700 p-4 rounded-lg">
            <h3 className="font-bold mb-3">Job Status</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span>Generated</span>
                <span className="font-bold text-yellow-400">0/100</span>
              </div>
              <div className="w-full bg-slate-600 rounded-full h-2">
                <div className="bg-yellow-500 h-2 rounded-full" style={{ width: "0%" }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === "history" && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold mb-4">Generated Content History</h2>
          <p className="text-slate-400">Recent content will appear here.</p>
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-slate-700 p-4 rounded-lg">
                <p className="text-xs text-slate-400 mb-2">Product Title</p>
                <p className="text-sm mb-2">Generated content sample...</p>
                <div className="flex gap-2">
                  <span className="text-xs bg-green-900 text-green-300 px-2 py-1 rounded">SEO: 85</span>
                  <span className="text-xs bg-blue-900 text-blue-300 px-2 py-1 rounded">Engage: 78</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContentGenerator;
