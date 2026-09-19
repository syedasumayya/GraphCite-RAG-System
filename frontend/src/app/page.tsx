"use client";
import { useState, FormEvent } from "react";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: { id: number; text: string; filename: string }[];
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  
  // Document History State
  const [currentPdf, setCurrentPdf] = useState("");
  const [pdfHistory, setPdfHistory] = useState<string[]>([]);

  const handleUpload = async (e: FormEvent<HTMLInputElement>) => {
    const file = e.currentTarget.files?.[0];
    if (!file) return;
    
    setUploadStatus("Ingesting & Chunking PDF...");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload", { method: "POST", body: formData });
      const data = await res.json();
      setUploadStatus(data.message);
      
      // Add to history and set as active
      setCurrentPdf(file.name);
      setPdfHistory((prev) => prev.includes(file.name) ? prev : [...prev, file.name]);
      setMessages([]); // Clear chat for new document
    } catch (error) {
      setUploadStatus("Error uploading file.");
    }
  };

  const switchPdf = (filename: string) => {
    setCurrentPdf(filename);
    setMessages([]); // Clear chat when switching documents
    setUploadStatus(`Switched to ${filename}`);
  };

  const handleChat = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: input,
          history: newMessages.map(m => ({ role: m.role, content: m.content })),
          filename: currentPdf // Send the active PDF filename
        })
      });
      
      const data = await res.json();
      
      const aiMessage: Message = { 
        role: "assistant", 
        content: data.answer, 
        citations: data.citations 
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: "Error connecting to API." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
      
      {/* LEFT PANEL: Chat Interface */}
      <div className="flex-1 flex flex-col border-r border-slate-700">
        <header className="p-4 bg-slate-900 border-b border-slate-700 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-blue-400">GraphCite</h1>
            <p className="text-xs text-slate-500">Advanced RAG System</p>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="h-full flex items-center justify-center text-center">
              <div>
                <h2 className="text-3xl font-bold text-slate-300 mb-3">Welcome to GraphCite</h2>
                <p className="text-slate-500 mb-8 max-w-md mx-auto">Upload a PDF or select one from your history to start asking questions.</p>
                <div className="flex justify-center gap-4 text-sm text-slate-400">
                  <div className="flex items-center gap-2 bg-slate-800 px-4 py-2 rounded-full"><span>🔍</span> Smart Retrieval</div>
                  <div className="flex items-center gap-2 bg-slate-800 px-4 py-2 rounded-full"><span>📑</span> Accurate Citations</div>
                  <div className="flex items-center gap-2 bg-slate-800 px-4 py-2 rounded-full"><span>🛡️</span> Reliable Answers</div>
                </div>
              </div>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] p-4 rounded-xl ${msg.role === "user" ? "bg-blue-600" : "bg-slate-800 border border-slate-700"}`}>
                {msg.role === "assistant" ? (
                  <div className="text-sm prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm">{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          {isLoading && <div className="text-slate-400 text-sm animate-pulse">● ● ● Thinking...</div>}
        </div>

        <form onSubmit={handleChat} className="p-4 bg-slate-900 border-t border-slate-700 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 p-3 bg-slate-800 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <button type="submit" disabled={isLoading} className="px-6 py-3 bg-blue-600 rounded-xl font-medium hover:bg-blue-500 transition disabled:opacity-50 text-sm">
            Send
          </button>
        </form>
      </div>

      {/* RIGHT PANEL: History, Upload & Citations */}
      <div className="w-96 bg-slate-950 border-l border-slate-700 flex flex-col">
        
        {/* Upload Section */}
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Upload Document</h2>
          <label className="cursor-pointer text-sm px-4 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg transition flex items-center justify-center gap-2">
            📄 Choose PDF File
            <input type="file" accept=".pdf" onChange={handleUpload} className="hidden" />
          </label>
          {uploadStatus && <p className="text-sm text-green-400 mt-3 text-center">{uploadStatus}</p>}
        </div>

        {/* Document History Section */}
        <div className="p-4 border-b border-slate-700">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Document History</h2>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {pdfHistory.length === 0 ? (
              <p className="text-xs text-slate-600">No documents uploaded yet.</p>
            ) : (
              pdfHistory.map((pdf, idx) => (
                <button 
                  key={idx} 
                  onClick={() => switchPdf(pdf)}
                  className={`w-full text-left text-xs p-2 rounded-lg flex items-center gap-2 transition ${currentPdf === pdf ? "bg-blue-600/30 text-blue-400 border border-blue-500" : "bg-slate-900 text-slate-400 hover:bg-slate-800"}`}
                >
                  <span>📄</span> <span className="truncate">{pdf}</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Citations Section */}
        <div className="flex-1 overflow-y-auto p-4">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">Retrieved Sources & Citations</h2>
          
          {messages.filter(m => m.citations).length === 0 ? (
            <div className="text-center text-slate-600 text-sm mt-10">
              <p className="font-bold text-slate-500">0 sources</p>
              <p>No sources yet. Ask a question to view retrieved documents!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.filter(m => m.citations).map((msg, idx) => (
                <div key={idx} className="space-y-3 border-b border-slate-800 pb-4">
                  <h3 className="text-xs font-bold text-blue-400">Sources for Answer:</h3>
                  {msg.citations?.map((cit) => (
                    <div key={cit.id} className="p-3 bg-slate-900 rounded-lg border-l-2 border-blue-500">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="bg-blue-600 text-xs px-2 py-0.5 rounded-full font-bold">[{cit.id}]</span>
                        <span className="text-xs text-slate-400 truncate">{cit.filename}</span>
                      </div>
                      <pre className="text-xs text-slate-400 whitespace-pre-wrap font-sans">{cit.text.substring(0, 200)}...</pre>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}