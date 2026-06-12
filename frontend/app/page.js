"use client";

import { useState } from "react";

const users = [
  { username: "dr.mehta", password: "doctor", role: "doctor" },
  { username: "nurse.priya", password: "nurse", role: "nurse" },
  { username: "billing.ravi", password: "billing", role: "billing_executive" },
  { username: "tech.anand", password: "technician", role: "technician" },
  { username: "admin.sys", password: "admin", role: "admin" },
];

export default function Home() {
  const [selectedUser, setSelectedUser] = useState(users[1]);
  const [question, setQuestion] = useState("What is the leave policy?");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function askQuestion() {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
          role: selectedUser.role,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        answer: "Could not connect to backend. Make sure FastAPI is running.",
        sources: [],
        retrieval_type: "error",
        role: selectedUser.role,
      });
    }

    setLoading(false);
  }

  return (
    <main className="min-h-screen bg-gray-100 p-8 text-gray-900">
      <div className="mx-auto max-w-4xl rounded-2xl bg-white p-8 shadow">
        <h1 className="mb-2 text-3xl font-bold">MediBot</h1>
        <p className="mb-6 text-gray-600">
          Role-aware RAG assistant for MediAssist Health Network
        </p>

        <label className="mb-2 block font-semibold">Demo user</label>
        <select
          className="mb-4 w-full rounded border p-3"
          value={selectedUser.username}
          onChange={(event) => {
            const user = users.find((u) => u.username === event.target.value);
            setSelectedUser(user);
          }}
        >
          {users.map((user) => (
            <option key={user.username} value={user.username}>
              {user.username} — {user.role}
            </option>
          ))}
        </select>

        <div className="mb-4 rounded bg-blue-50 p-3">
          <strong>Current role:</strong> {selectedUser.role}
        </div>

        <label className="mb-2 block font-semibold">Question</label>
        <textarea
          className="mb-4 h-28 w-full rounded border p-3"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />

        <button
          onClick={askQuestion}
          disabled={loading}
          className="rounded bg-blue-600 px-5 py-3 font-semibold text-white disabled:bg-gray-400"
        >
          {loading ? "Thinking..." : "Ask MediBot"}
        </button>

        {result && (
          <div className="mt-8 rounded border p-5">
            <div className="mb-3 flex gap-3">
              <span className="rounded bg-green-100 px-3 py-1 text-sm">
                Role: {result.role}
              </span>
              <span className="rounded bg-purple-100 px-3 py-1 text-sm">
                Retrieval: {result.retrieval_type}
              </span>
            </div>

            <h2 className="mb-2 text-xl font-bold">Answer</h2>
            <div className="whitespace-pre-wrap rounded bg-gray-50 p-4">
              {result.answer}
            </div>

            <h2 className="mb-2 mt-6 text-xl font-bold">Sources</h2>
            {result.sources?.length > 0 ? (
              <ul className="space-y-2">
                {result.sources.map((source, index) => (
                  <li key={index} className="rounded bg-gray-50 p-3">
                    <strong>{source.source_document}</strong>
                    <br />
                    Section: {source.section_title}
                    <br />
                    Collection: {source.collection}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No sources returned.</p>
            )}

            {result.sql && (
              <>
                <h2 className="mb-2 mt-6 text-xl font-bold">SQL Used</h2>
                <pre className="overflow-x-auto rounded bg-gray-900 p-4 text-white">
                  {result.sql}
                </pre>
              </>
            )}
          </div>
        )}
      </div>
    </main>
  );
}