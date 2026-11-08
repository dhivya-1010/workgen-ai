import { useEffect, useMemo, useState } from "react";
import {
  createInstitutionalAnswer,
  deleteInstitutionalDocument,
  getInstitutionalAnswers,
  getInstitutionalDashboard,
  getInstitutionalDocuments,
  searchInstitutionalKnowledge,
  submitInstitutionalAnswer,
  updateInstitutionalAnswer,
  uploadInstitutionalDocument,
} from "../services/api";

const TABS = [
  ["knowledge", "Knowledge Hub"],
  ["faculty", "Faculty Portal"],
  ["student", "AI Study Buddy"],
  ["admin", "Institution Admin"],
];

export default function InstitutionalPlatform({ theme }) {
  const dark = theme === "dark";
  const [tab, setTab] = useState("knowledge");
  const [documents, setDocuments] = useState([]);
  const [answers, setAnswers] = useState([]);
  const [dashboard, setDashboard] = useState({});
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [question, setQuestion] = useState("");
  const [subject, setSubject] = useState("");
  const [unit, setUnit] = useState("");
  const [selectedAnswer, setSelectedAnswer] = useState("");
  const [studentAnswer, setStudentAnswer] = useState("");
  const [message, setMessage] = useState("");

  const refresh = async () => {
    const [docs, answerData, stats] = await Promise.all([
      getInstitutionalDocuments(),
      getInstitutionalAnswers(),
      getInstitutionalDashboard(),
    ]);
    setDocuments(docs.documents || []);
    setAnswers(answerData.answers || []);
    setDashboard(stats || {});
  };

  useEffect(() => {
    refresh().catch((error) => setMessage(error.message));
  }, []);

  const card = `rounded-3xl border p-5 ${dark ? "border-white/10 bg-white/5" : "border-[#D3CBB8] bg-white/80"}`;
  const visibleAnswers = useMemo(
    () => answers.filter((answer) => tab === "student" ? ["approved", "published"].includes(answer.status) : true),
    [answers, tab],
  );

  async function upload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await uploadInstitutionalDocument(file, { subject, unit });
      setMessage(`${file.name} added to the institutional knowledge base.`);
      await refresh();
    } catch (error) {
      setMessage(error.message);
    }
    event.target.value = "";
  }

  async function search(event) {
    event.preventDefault();
    try {
      const data = await searchInstitutionalKnowledge(query, subject, unit);
      setResults(data.results || []);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function generate(event) {
    event.preventDefault();
    try {
      await createInstitutionalAnswer({ question, subject, unit, marks: 10 });
      setQuestion("");
      setMessage("Traceable answer draft created for faculty review.");
      await refresh();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function approve(answer) {
    try {
      await updateInstitutionalAnswer(answer.id, { status: "approved" });
      setMessage("Answer approved and available to students.");
      await refresh();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function submit(event) {
    event.preventDefault();
    try {
      const data = await submitInstitutionalAnswer({ answer_id: selectedAnswer, student_answer: studentAnswer });
      setMessage(`Evaluation: ${data.score}% — ${data.feedback}`);
      setStudentAnswer("");
    } catch (error) {
      setMessage(error.message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-5">
        {[
          ["Documents", dashboard.documents || 0],
          ["Indexed chunks", dashboard.chunks || 0],
          ["Draft answers", dashboard.draft_answers || 0],
          ["Approved answers", dashboard.approved_answers || 0],
          ["Submissions", dashboard.submissions || 0],
        ].map(([label, value]) => <div className={card} key={label}><p className="text-xs uppercase tracking-widest opacity-60">{label}</p><p className="mt-2 text-3xl font-semibold">{value}</p></div>)}
      </div>

      <div className={`${card} flex flex-wrap gap-2`}>
        {TABS.map(([id, label]) => <button key={id} onClick={() => setTab(id)} className={`rounded-2xl px-4 py-3 text-sm font-semibold ${tab === id ? "bg-amber-400 text-slate-950" : dark ? "bg-white/10" : "bg-stone-100"}`}>{label}</button>)}
      </div>

      {message && <div className={`${card} border-amber-400/40 text-sm`}>{message}</div>}

      {tab === "knowledge" && <div className="grid gap-6 lg:grid-cols-2">
        <section className={`${card} space-y-4`}>
          <h3 className="text-xl font-semibold">Institutional document ingestion</h3>
          <p className="text-sm opacity-70">Upload PDF, DOCX, PPTX, scanned PDF, TXT, MD or CSV resources. Text is extracted, chunked and indexed with source metadata.</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <input className="field" placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} />
            <input className="field" placeholder="Unit" value={unit} onChange={(e) => setUnit(e.target.value)} />
          </div>
          <label className="button-primary inline-block cursor-pointer">Upload resource<input className="hidden" type="file" accept=".pdf,.docx,.pptx,.txt,.md,.csv" onChange={upload} /></label>
          <div className="space-y-2">{documents.map((doc) => <div className="flex items-center justify-between rounded-2xl border border-white/10 p-3 text-sm" key={doc.id}><span><b>{doc.filename}</b><br /><span className="opacity-60">{doc.subject || "Uncategorized"} {doc.unit && `· ${doc.unit}`}</span></span><button className="text-red-400" onClick={async () => { await deleteInstitutionalDocument(doc.id); refresh(); }}>Remove</button></div>)}</div>
        </section>
        <section className={`${card} space-y-4`}>
          <h3 className="text-xl font-semibold">Semantic source search</h3>
          <form onSubmit={search} className="flex gap-2"><input className="field flex-1" placeholder="Search the syllabus and resources" value={query} onChange={(e) => setQuery(e.target.value)} /><button className="button-primary">Search</button></form>
          {results.map((result) => <article className="rounded-2xl border border-white/10 p-4" key={`${result.source.document_id}-${result.source.chunk}`}><p className="text-sm">{result.text}</p><p className="mt-2 text-xs opacity-60">Source: {result.source.filename} · chunk {result.source.chunk} · score {result.score}</p></article>)}
        </section>
      </div>}

      {tab === "faculty" && <div className="grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        <section className={`${card} space-y-4`}><h3 className="text-xl font-semibold">Canonical Answer Engine</h3><p className="text-sm opacity-70">Generate a syllabus-scoped, source-traceable draft for review.</p><form onSubmit={generate} className="space-y-3"><input className="field w-full" placeholder="Question" value={question} onChange={(e) => setQuestion(e.target.value)} required /><input className="field w-full" placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} /><input className="field w-full" placeholder="Unit" value={unit} onChange={(e) => setUnit(e.target.value)} /><button className="button-primary">Generate draft</button></form></section>
        <AnswerList answers={visibleAnswers} onApprove={approve} dark={dark} />
      </div>}

      {tab === "student" && <div className="grid gap-6 lg:grid-cols-2">
        <AnswerList answers={visibleAnswers} onApprove={approve} dark={dark} student onSelect={setSelectedAnswer} selected={selectedAnswer} />
        <section className={`${card} space-y-4`}><h3 className="text-xl font-semibold">Answer evaluation</h3><p className="text-sm opacity-70">Submit against a faculty-approved canonical answer to receive rubric-style coverage feedback.</p><form onSubmit={submit} className="space-y-3"><textarea className="field min-h-48 w-full" placeholder="Write your answer here" value={studentAnswer} onChange={(e) => setStudentAnswer(e.target.value)} required /><button className="button-primary" disabled={!selectedAnswer}>Evaluate response</button></form></section>
      </div>}

      {tab === "admin" && <section className={`${card} space-y-4`}><h3 className="text-xl font-semibold">Institution administration</h3><p className="text-sm opacity-70">The platform is ready for institution, department, course and role records. Uploaded resources and answer publication remain auditable through the dashboard counters and source metadata.</p><div className="grid gap-3 sm:grid-cols-3">{["institutions", "departments", "courses"].map((key) => <div className="rounded-2xl border border-white/10 p-4" key={key}><p className="text-xs uppercase tracking-widest opacity-60">{key}</p><p className="mt-2 text-2xl font-semibold">{dashboard[key]?.length || 0}</p></div>)}</div></section>}
    </div>
  );
}

function AnswerList({ answers, onApprove, student, onSelect, selected, dark }) {
  return <section className={`rounded-3xl border p-5 ${dark ? "border-white/10 bg-white/5" : "border-[#D3CBB8] bg-white/80"} space-y-3`}><h3 className="text-xl font-semibold">{student ? "Approved standard answers" : "Answer review queue"}</h3>{answers.length === 0 && <p className="text-sm opacity-60">No answers yet. Add documents and generate a draft.</p>}{answers.map((answer) => <article className={`rounded-2xl border p-4 ${selected === answer.id ? "border-amber-400" : "border-white/10"}`} key={answer.id} onClick={() => student && onSelect(answer.id)}><div className="flex items-center justify-between gap-3"><b>{answer.question}</b><span className="text-xs uppercase opacity-60">{answer.status}</span></div><p className="mt-2 line-clamp-4 text-sm opacity-80">{answer.answer}</p><p className="mt-2 text-xs opacity-60">{answer.sources?.length || 0} cited source chunks · version {answer.version}</p>{!student && answer.status === "draft" && <button className="button-secondary mt-3" onClick={() => onApprove(answer)}>Approve & publish</button>}</article>)}</section>;
}
