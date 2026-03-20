"use client";

import { useSession } from "next-auth/react";
import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, CheckCircle, Clock, XCircle, Trash2 } from "lucide-react";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface Document {
  id: string;
  filename: string;
  status: string;
  page_count: number;
  created_at: string;
}

export default function UploadPage() {
  const { data: session } = useSession();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const token = (session as any)?.accessToken;

  const fetchDocuments = useCallback(async () => {
    if (!token) return;
    const res = await fetch(`${BACKEND_URL}/api/documents/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setDocuments(await res.json());
  }, [token]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (!token) return;
      setError("");
      setUploading(true);

      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append("file", file);

        try {
          await fetch(`${BACKEND_URL}/api/documents/upload`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          });
        } catch {
          setError(`${file.name} のアップロードに失敗しました`);
        }
      }

      setUploading(false);
      fetchDocuments();
    },
    [token, fetchDocuments]
  );

  const deleteDocument = async (id: string) => {
    await fetch(`${BACKEND_URL}/api/documents/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    fetchDocuments();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    maxSize: 50 * 1024 * 1024,
  });

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle size={16} className="text-green-500" />;
      case "processing": return <Clock size={16} className="text-yellow-500 animate-spin" />;
      case "failed": return <XCircle size={16} className="text-red-500" />;
      default: return <Clock size={16} className="text-gray-400" />;
    }
  };

  const statusLabel = (status: string) => {
    switch (status) {
      case "completed": return "完了";
      case "processing": return "処理中";
      case "failed": return "失敗";
      default: return "待機中";
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-lg font-semibold text-gray-800 mb-6">謄本アップロード</h2>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400"
        }`}
      >
        <input {...getInputProps()} />
        <Upload size={40} className="mx-auto text-gray-400 mb-4" />
        {uploading ? (
          <p className="text-gray-600">アップロード中...</p>
        ) : isDragActive ? (
          <p className="text-blue-600">ここにドロップしてください</p>
        ) : (
          <>
            <p className="text-gray-600">PDFファイルをドラッグ＆ドロップ</p>
            <p className="text-sm text-gray-400 mt-1">またはクリックして選択（最大50MB）</p>
          </>
        )}
      </div>

      {error && <div className="mt-4 bg-red-50 text-red-600 p-3 rounded-lg text-sm">{error}</div>}

      <div className="mt-8">
        <h3 className="text-md font-medium text-gray-700 mb-4">アップロード済み謄本</h3>
        {documents.length === 0 ? (
          <p className="text-gray-400 text-sm">まだ謄本がアップロードされていません</p>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex items-center gap-3">
                  <FileText size={20} className="text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{doc.filename}</p>
                    <p className="text-xs text-gray-500">
                      {doc.page_count > 0 && `${doc.page_count}ページ · `}
                      {new Date(doc.created_at).toLocaleDateString("ja-JP")}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1 text-xs">
                    {statusIcon(doc.status)}
                    {statusLabel(doc.status)}
                  </span>
                  <button onClick={() => deleteDocument(doc.id)} className="text-gray-400 hover:text-red-500">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
