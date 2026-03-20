"use client";

import { useSession } from "next-auth/react";
import { useCallback, useEffect, useState } from "react";
import { Users, FileText, Activity, Plus, Trash2 } from "lucide-react";
import { BACKEND_URL } from "@/lib/api";

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  details: Record<string, any>;
  ip_address: string | null;
  created_at: string;
}

export default function AdminPage() {
  const { data: session } = useSession();
  const [tab, setTab] = useState<"users" | "documents" | "logs">("users");
  const [users, setUsers] = useState<User[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [stats, setStats] = useState({ user_count: 0, document_count: 0 });
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", email: "", password: "", role: "user" });

  const token = (session as any)?.accessToken;

  const fetchData = useCallback(async () => {
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };

    const [usersRes, statsRes, logsRes] = await Promise.all([
      fetch(`${BACKEND_URL}/api/admin/users`, { headers }),
      fetch(`${BACKEND_URL}/api/admin/stats`, { headers }),
      fetch(`${BACKEND_URL}/api/admin/logs?limit=50`, { headers }),
    ]);

    if (usersRes.ok) setUsers(await usersRes.json());
    if (statsRes.ok) setStats(await statsRes.json());
    if (logsRes.ok) setLogs(await logsRes.json());
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const createUser = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch(`${BACKEND_URL}/api/admin/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(newUser),
    });
    setShowCreateUser(false);
    setNewUser({ username: "", email: "", password: "", role: "user" });
    fetchData();
  };

  const toggleUser = async (userId: string, isActive: boolean) => {
    await fetch(`${BACKEND_URL}/api/admin/users/${userId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ is_active: !isActive }),
    });
    fetchData();
  };

  const deleteUser = async (userId: string) => {
    if (!confirm("このユーザーを削除しますか？")) return;
    await fetch(`${BACKEND_URL}/api/admin/users/${userId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    fetchData();
  };

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-6">管理者画面</h2>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-3">
          <Users size={24} className="text-blue-500" />
          <div>
            <p className="text-2xl font-bold text-gray-800">{stats.user_count}</p>
            <p className="text-xs text-gray-500">ユーザー数</p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-3">
          <FileText size={24} className="text-green-500" />
          <div>
            <p className="text-2xl font-bold text-gray-800">{stats.document_count}</p>
            <p className="text-xs text-gray-500">謄本数</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
        {[
          { key: "users" as const, label: "ユーザー管理", icon: Users },
          { key: "logs" as const, label: "ログ", icon: Activity },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-colors ${
              tab === t.key ? "bg-white shadow text-blue-700" : "text-gray-600"
            }`}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </div>

      {/* Users Tab */}
      {tab === "users" && (
        <div>
          <button
            onClick={() => setShowCreateUser(true)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm mb-4 hover:bg-blue-700"
          >
            <Plus size={16} /> ユーザー追加
          </button>

          {showCreateUser && (
            <form onSubmit={createUser} className="bg-white border border-gray-200 rounded-lg p-4 mb-4 grid grid-cols-2 gap-3">
              <input
                placeholder="ユーザー名"
                value={newUser.username}
                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
                required
              />
              <input
                placeholder="メールアドレス"
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
                required
              />
              <input
                placeholder="パスワード"
                type="password"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
                required
              />
              <select
                value={newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                className="px-3 py-2 border rounded-lg text-sm"
              >
                <option value="user">ユーザー</option>
                <option value="admin">管理者</option>
              </select>
              <div className="col-span-2 flex gap-2">
                <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm">作成</button>
                <button type="button" onClick={() => setShowCreateUser(false)} className="text-gray-600 px-4 py-2 text-sm">キャンセル</button>
              </div>
            </form>
          )}

          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">ユーザー名</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">メール</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">権限</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">状態</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b last:border-b-0">
                    <td className="px-4 py-3">{u.username}</td>
                    <td className="px-4 py-3 text-gray-500">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs ${u.role === "admin" ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-600"}`}>
                        {u.role === "admin" ? "管理者" : "ユーザー"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => toggleUser(u.id, u.is_active)} className={`px-2 py-0.5 rounded text-xs ${u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                        {u.is_active ? "有効" : "無効"}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => deleteUser(u.id)} className="text-gray-400 hover:text-red-500">
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {tab === "logs" && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">日時</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">アクション</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">IP</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">詳細</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b last:border-b-0">
                  <td className="px-4 py-3 text-gray-500">{new Date(log.created_at).toLocaleString("ja-JP")}</td>
                  <td className="px-4 py-3">{log.action}</td>
                  <td className="px-4 py-3 text-gray-500">{log.ip_address || "-"}</td>
                  <td className="px-4 py-3 text-gray-500 truncate max-w-xs">{JSON.stringify(log.details)}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">ログがありません</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
