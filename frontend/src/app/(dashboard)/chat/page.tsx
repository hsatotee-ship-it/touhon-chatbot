"use client";

import { useSession } from "next-auth/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { BACKEND_URL } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ index: number; filename: string; similarity: number }>;
}

export default function ChatPage() {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const token = (session as any)?.accessToken;
      const res = await fetch(`${BACKEND_URL}/api/chat/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId,
        }),
      });

      if (!res.ok) throw new Error("送信に失敗しました");
      const data = await res.json();

      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `エラー: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, session, sessionId]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-gray-800">謄本チャット</h2>
        <p className="text-sm text-gray-500">アップロードした謄本について質問できます</p>
      </div>

      <div className="flex-1 overflow-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <p className="text-lg">謄本について質問してください</p>
            <p className="text-sm mt-2">例：「この物件の所有者は誰ですか？」</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-200 text-gray-800"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}

              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-100">
                  <p className="text-xs text-gray-500 font-medium mb-1">出典:</p>
                  {msg.sources.map((src) => (
                    <span
                      key={src.index}
                      className="inline-block text-xs bg-gray-100 text-gray-600 rounded px-2 py-0.5 mr-1 mb-1"
                    >
                      [{src.index}] {src.filename} ({(src.similarity * 100).toFixed(0)}%)
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 px-6 py-4">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="質問を入力してください..."
            rows={1}
            className="flex-1 resize-none px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="bg-blue-600 text-white p-2.5 rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
