import { useMemo, useState } from 'react'
import ApiResponsePanel from '../components/ApiResponsePanel'
import ResultCard from '../components/ResultCard'
import { runEmailAction, scanEmails } from '../services/api'
import { shareViaEmail } from '../utils/exportPdf'
import { usePageState } from '../context/PageStateContext'

function normalizeEmailScan(data) {
  return {
    emails: data?.detected_emails || data?.emails || [],
    events: data?.upcoming_events || data?.events || data?.calendar || [],
    scannedCount: data?.scanned_count || data?.count || 0,
  }
}

function typeTone(type, theme) {
  const dark = theme === 'dark'
  const value = String(type || 'Unknown').toLowerCase()
  if (dark) {
    if (value.includes('meeting')) return 'bg-sky-500/15 text-sky-300 border-sky-400/30'
    if (value.includes('task')) return 'bg-amber-500/15 text-amber-300 border-amber-400/30'
    if (value.includes('exam')) return 'bg-rose-500/15 text-rose-300 border-rose-400/30'
    return 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30'
  } else {
    if (value.includes('meeting')) return 'bg-forest/10 text-forest border-forest/30 font-semibold'
    if (value.includes('task')) return 'bg-clay/10 text-clay border-clay/30 font-semibold'
    if (value.includes('exam')) return 'bg-rose-700/10 text-rose-700 border-rose-700/30 font-semibold'
    return 'bg-forest/10 text-forest border-forest/30 font-semibold'
  }
}

export default function EmailIntelligence({ theme }) {
  const [pageState, setPageState] = usePageState("email-intelligence");
  const payload = pageState?.payload ?? { emails: [], events: [], scannedCount: 0 };
  const setPayload = (v) => setPageState((s) => ({ ...s, payload: typeof v === 'function' ? v(s?.payload ?? { emails: [], events: [], scannedCount: 0 }) : v }));
  const [loading, setLoading] = useState(false);
  const [rawResponse, setRawResponse] = useState(null);
  const [error, setError] = useState('')
  const [actionMessage, setActionMessage] = useState('')
  const [busyAction, setBusyAction] = useState('')

  const summary = useMemo(() => ({
    meetings: payload.emails.filter((item) => String(item.detected_type || item.type).toLowerCase().includes('meeting')).length,
    tasks: payload.emails.filter((item) => String(item.detected_type || item.type).toLowerCase().includes('task')).length,
  }), [payload.emails])

  const scan = async () => {
    setLoading(true)
    setError('')
    setActionMessage('')

    try {
      const response = await scanEmails()
      setRawResponse(response)
      if (response?.error) {
        setError(response.error)
      }
      setPayload(normalizeEmailScan(response))
    } catch (err) {
      setError(err.message || 'Unable to scan emails.')
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (action, email, index) => {
    const key = `${action}-${index}`
    setBusyAction(key)
    setActionMessage('')
    setError('')

    try {
      const response = await runEmailAction(action, email)
      setRawResponse(response)
      setActionMessage(`${action === 'calendar' ? 'Calendar' : 'Notion'} action submitted for “${email.subject || 'Untitled'}”.`)
    } catch (err) {
      setError(err.message || `Unable to complete ${action} action.`)
    } finally {
      setBusyAction('')
    }
  }

  const handleShareSingleEmail = (email) => {
    const subject = `[Email Signal] ${email.subject || email.sender || 'Email Insight'}`
    const body = `Hi,\n\nHere is an email insight captured by AgentX Email Intelligence:\n\nSubject: ${email.subject || 'N/A'}\nFrom: ${email.sender || email.from || 'N/A'}\nType: ${email.detected_type || email.type || 'N/A'}\nSummary/Preview: ${email.preview || email.snippet || email.body || 'N/A'}\n\n---\nSent via AgentX Email Intelligence`
    shareViaEmail({ subject, body })
  }

  const handleShareAllEmails = () => {
    if (!payload.emails.length) return
    const subject = `AgentX Email Intelligence Scan Report (${payload.emails.length} signals)`
    const emailSummaries = payload.emails
      .map((e, i) => `${i + 1}. [${e.detected_type || e.type || 'Signal'}] ${e.subject || 'Untitled'} - ${e.sender || e.from || 'Unknown'}\n   ${e.preview || e.snippet || ''}`)
      .join('\n\n')
    const body = `Hi,\n\nHere is the Email Intelligence Scan Summary:\n\nTotal Signals: ${payload.emails.length}\nMeetings Detected: ${summary.meetings}\nTasks Detected: ${summary.tasks}\n\n=== EMAIL SIGNALS ===\n${emailSummaries}\n\n---\nSent via AgentX Email Intelligence`
    shareViaEmail({ subject, body })
  }

  const cardClass = theme === 'dark' ? 'border-white/10 bg-white/5' : 'border-[#D3CBB8] bg-[#FAF8F5]'

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-3">
        {[
          { label: 'Scanned Emails', value: payload.scannedCount || payload.emails.length },
          { label: 'Meeting Signals', value: summary.meetings },
          { label: 'Task Signals', value: summary.tasks },
        ].map((stat) => (
          <div key={stat.label} className={`rounded-[28px] border p-5 shadow-xl ${cardClass}`}>
            <p className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-stone-500'}`}>{stat.label}</p>
            <p className="mt-3 text-3xl font-semibold">{stat.value}</p>
          </div>
        ))}
      </section>

      <ResultCard
        title="Email Intelligence"
        subtitle="Scan Gmail, classify intent, and surface calendar-ready opportunities."
        theme={theme}
        actions={
          <div className="flex flex-wrap gap-2">
            {payload.emails.length > 0 ? (
              <button
                type="button"
                onClick={handleShareAllEmails}
                className={`flex items-center gap-2 rounded-2xl border px-4 py-2 text-sm font-semibold transition ${
                  theme === 'dark'
                    ? 'border-purple-500/30 bg-purple-500/10 text-purple-300 hover:bg-purple-500/20'
                    : 'border-clay/30 bg-clay/10 text-clay hover:bg-clay/20'
                }`}
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 002-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Share Scan via Email
              </button>
            ) : null}
            <button
              type="button"
              onClick={scan}
              disabled={loading}
              className={`rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
                theme === 'dark' ? 'bg-cyan-400 text-slate-950 hover:bg-cyan-300' : 'bg-clay text-white hover:bg-clay/90'
              }`}
            >
              {loading ? 'Scanning…' : 'Scan Emails'}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          {error ? <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div> : null}
          {actionMessage ? <div className="rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300">{actionMessage}</div> : null}
        </div>
      </ResultCard>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.85fr]">
        <ResultCard title="Detected Emails" subtitle="AI classified emails ready for action." theme={theme}>
          <div className="space-y-4">
            {payload.emails.length === 0 ? (
              <div className={`rounded-3xl border border-dashed p-8 text-center text-sm text-slate-400 ${cardClass}`}>
                Click <span className="font-semibold text-slate-200">Scan Emails</span> to load classified inbox results.
              </div>
            ) : (
              payload.emails.map((email, index) => {
                const type = email.detected_type || email.type || 'Unknown'
                return (
                  <div key={`${email.subject || 'email'}-${index}`} className={`rounded-3xl border p-5 ${cardClass}`}>
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div className="space-y-2">
                        <div className="text-lg font-semibold">{email.subject || 'Untitled Email'}</div>
                        <div className={`text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-stone-500'}`}>{email.sender || email.from || 'Unknown sender'}</div>
                      </div>
                      <div className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${typeTone(type, theme)}`}>
                        {type}
                      </div>
                    </div>

                    <p className={`mt-4 text-sm leading-7 ${theme === 'dark' ? 'text-slate-400' : 'text-stone-700'}`}>
                      {email.preview || email.snippet || email.body || 'No email preview returned by the backend.'}
                    </p>

                    <div className="mt-5 flex flex-wrap gap-3">
                      <button
                        type="button"
                        onClick={() => handleAction('calendar', email, index)}
                        disabled={busyAction === `calendar-${index}`}
                        className={`rounded-2xl px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${
                          theme === 'dark'
                            ? 'bg-slate-900/80 text-white ring-1 ring-white/10 hover:bg-slate-800'
                            : 'bg-[#2F5D50] text-white hover:bg-forest/90'
                        }`}
                      >
                        {busyAction === `calendar-${index}` ? 'Adding…' : 'Add to Calendar'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleAction('notion', email, index)}
                        disabled={busyAction === `notion-${index}`}
                        className={`rounded-2xl border px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${
                          theme === 'dark'
                            ? 'border-cyan-400/30 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/15'
                            : 'border-clay/30 bg-clay/10 text-clay hover:bg-clay/15'
                        }`}
                      >
                        {busyAction === `notion-${index}` ? 'Saving…' : 'Save to Notion'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleShareSingleEmail(email)}
                        className={`flex items-center gap-1.5 rounded-2xl border px-4 py-2 text-sm font-medium transition ${
                          theme === 'dark'
                            ? 'border-purple-400/30 bg-purple-500/10 text-purple-300 hover:bg-purple-500/15'
                            : 'border-clay/30 bg-clay/10 text-clay hover:bg-clay/15'
                        }`}
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 002-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        Share via Email
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </ResultCard>

        <ResultCard title="Upcoming Events"  theme={theme}>
          <div className="space-y-3">
            {payload.events.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 px-4 py-5 text-sm text-slate-400">
                Upcoming events will appear here after the scan returns calendar data.
              </div>
            ) : (
              payload.events.map((event, index) => (
                <div key={`${event.title || event.summary || 'event'}-${index}`} className={`rounded-2xl border p-4 ${cardClass}`}>
                  <div className="font-semibold">{event.title || event.summary || 'Untitled event'}</div>
                  <div className={`mt-1 text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-stone-500'}`}>{event.datetime || event.start_time || event.start || 'Time not provided'}</div>
                  <div className={`mt-3 text-xs uppercase tracking-[0.2em] ${theme === 'dark' ? 'text-cyan-400' : 'text-forest font-semibold'}`}>{event.source || 'calendar sync'}</div>
                </div>
              ))
            )}
          </div>
        </ResultCard>
      </div>

      {/* <ApiResponsePanel data={rawResponse} theme={theme} /> */}
    </div>
  )
}