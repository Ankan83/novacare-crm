import { useEffect, useMemo, useState } from "react";
import { useSelector } from "react-redux";

import {
  checkCompliance,
  downloadCalendarEvent,
  findDuplicateHcps,
  getFollowUpEmail,
  getAnalytics,
  getFollowUps,
  getMeetingPrep,
  getTimeline,
} from "../../api";
import "../../styles/CRMInsights.css";

function formatDate(value) {
  if (!value) return "No date";
  return new Date(value).toLocaleDateString();
}

function formatFollowUp(item) {
  if (!item.follow_up_date) {
    return item.follow_up || "Date not specified";
  }

  const resolvedDate = new Date(`${item.follow_up_date}T00:00:00`);
  const formattedDate = resolvedDate.toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return `Due ${formattedDate}`;
}

export default function CRMInsights() {
  const { interactionDraft, saved } = useSelector((state) => state.crm);
  const [analytics, setAnalytics] = useState(null);
  const [followUps, setFollowUps] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [meetingPrep, setMeetingPrep] = useState(null);
  const [compliance, setCompliance] = useState(null);
  const [duplicates, setDuplicates] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [emailDraft, setEmailDraft] = useState(null);

  const hcpId = interactionDraft.hcp_id;
  const hcpKey = useMemo(() => (hcpId ? String(hcpId) : ""), [hcpId]);

  useEffect(() => {
    let active = true;

    async function loadInsights() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled([
          getAnalytics(),
          getFollowUps(),
          getTimeline(hcpKey),
        ]);

        if (!active) return;

        const [analyticsResult, followUpResult, timelineResult] = results;
        if (analyticsResult.status === "fulfilled") {
          setAnalytics(analyticsResult.value);
        }
        if (followUpResult.status === "fulfilled") {
          setFollowUps(followUpResult.value.items ?? []);
        }
        if (timelineResult.status === "fulfilled") {
          setTimeline(timelineResult.value.items ?? []);
        }

        const failedRequest = results.find(
          (result) => result.status === "rejected",
        );
        if (failedRequest?.reason) {
          setError(failedRequest.reason.message);
        }

        if (hcpKey) {
          setMeetingPrep(await getMeetingPrep(hcpKey));
        } else {
          setMeetingPrep(null);
        }
      } catch (loadError) {
        if (active) setError(loadError.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadInsights();
    return () => {
      active = false;
    };
  }, [hcpKey, saved]);

  useEffect(() => {
    const text = [
      interactionDraft.subject,
      interactionDraft.notes,
      interactionDraft.follow_up,
    ]
      .filter(Boolean)
      .join(" ");

    if (!text) {
      setCompliance(null);
      return undefined;
    }

    let active = true;
    checkCompliance(text)
      .then((result) => {
        if (active) setCompliance(result);
      })
      .catch(() => {
        if (active) setCompliance(null);
      });

    return () => {
      active = false;
    };
  }, [
    interactionDraft.subject,
    interactionDraft.notes,
    interactionDraft.follow_up,
  ]);

  async function prepareEmail(item) {
    try {
      setEmailDraft(await getFollowUpEmail(item.interaction_id));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function addToCalendar(item) {
    if (!item.follow_up_date) {
      setError("This follow-up does not have a recognized date.");
      return;
    }
    try {
      const blob = await downloadCalendarEvent({
        title: item.action_item || "CRM follow-up",
        start_date: item.follow_up_date,
        description: item.follow_up,
        location: "",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "nova-follow-up.ics";
      link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  useEffect(() => {
    if (!interactionDraft.hcp_name) {
      setDuplicates(null);
      return undefined;
    }

    let active = true;
    findDuplicateHcps({
      full_name: interactionDraft.hcp_name,
      specialty: interactionDraft.hcp_specialty ?? "",
      organization: interactionDraft.hcp_organization ?? "",
      city: interactionDraft.hcp_city ?? "",
      exclude_id: hcpId ? Number(hcpId) : null,
    })
      .then((result) => {
        if (active) setDuplicates(result);
      })
      .catch(() => {
        if (active) setDuplicates(null);
      });

    return () => {
      active = false;
    };
  }, [
    interactionDraft.hcp_name,
    interactionDraft.hcp_specialty,
    interactionDraft.hcp_organization,
    interactionDraft.hcp_city,
    hcpId,
  ]);

  return (
    <section className="crm-insights">
      <div className="insights-heading">
        <div>
          <h2>CRM Copilot</h2>
          <p>Turn every interaction into your next best action.</p>
        </div>
        {loading && <span className="insights-loading">Refreshing...</span>}
      </div>

      {error && <p className="insights-error">{error}</p>}

      <div className="insights-metrics">
        <div>
          <strong>{analytics ? analytics.total_interactions : "—"}</strong>
          <span>Interactions</span>
        </div>
        <div>
          <strong>{analytics ? analytics.follow_ups : "—"}</strong>
          <span>Follow-ups</span>
        </div>
        <div>
          <strong>{analytics ? analytics.hcp_count : "—"}</strong>
          <span>HCPs</span>
        </div>
      </div>

      {duplicates?.is_duplicate && (
        <div className="insight-card warning-card">
          <h3>Possible duplicate HCP</h3>
          <p>
            {duplicates.matches[0].full_name} looks similar to this record
            ({Math.round(duplicates.matches[0].score * 100)}% match).
          </p>
        </div>
      )}

      {compliance && (
        <div className={`insight-card ${compliance.compliant ? "success-card" : "warning-card"}`}>
          <h3>{compliance.compliant ? "Compliance check passed" : "Review before saving"}</h3>
          {!compliance.compliant && (
            <ul>
              {compliance.findings.map((finding) => (
                <li key={finding.rule}>{finding.message}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {meetingPrep && (
        <div className="insight-card">
          <div className="card-title-row">
            <h3>Meeting preparation</h3>
            <span>{meetingPrep.interaction_count} interactions</span>
          </div>
          <p className="muted">
            {meetingPrep.hcp?.full_name} · {meetingPrep.hcp?.specialty} ·{" "}
            {meetingPrep.hcp?.city}
          </p>
          <div className="topic-list">
            {meetingPrep.key_topics.slice(0, 5).map((topic) => (
              <span key={topic}>{topic}</span>
            ))}
          </div>
          <ul className="question-list">
            {meetingPrep.suggested_questions.slice(0, 3).map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="insight-card">
        <div className="card-title-row">
          <h3>Follow-up copilot</h3>
          <span>{followUps.length} open</span>
        </div>
        {followUps.length === 0 ? (
          <p className="muted">No follow-up commitments yet.</p>
        ) : (
          <ul className="follow-up-list">
            {followUps.slice(0, 4).map((item) => (
              <li key={item.interaction_id}>
                <div>
                  <strong>
                    {item.action_item && item.action_item !== item.follow_up
                      ? item.action_item
                      : item.follow_up || "Follow-up"}
                  </strong>
                  <span>{formatFollowUp(item)}</span>
                </div>
                <div className="follow-up-actions">
                  <button type="button" onClick={() => prepareEmail(item)}>
                    Email draft
                  </button>
                  <button type="button" onClick={() => addToCalendar(item)}>
                    Calendar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {emailDraft && (
        <div className="insight-card email-draft-card">
          <div className="card-title-row">
            <h3>Follow-up email draft</h3>
            <button type="button" onClick={() => setEmailDraft(null)}>Close</button>
          </div>
          <strong>{emailDraft.subject}</strong>
          <pre>{emailDraft.body}</pre>
          <a
            className="email-link"
            href={`mailto:?subject=${encodeURIComponent(emailDraft.subject)}&body=${encodeURIComponent(emailDraft.body)}`}
          >
            Open in email app
          </a>
        </div>
      )}

      <div className="insight-card">
        <div className="card-title-row">
          <h3>Interaction timeline</h3>
          <span>{timeline.length} shown</span>
        </div>
        {timeline.length === 0 ? (
          <p className="muted">Saved interactions will appear here.</p>
        ) : (
          <div className="timeline">
            {timeline.slice(0, 5).map((item) => (
              <div className="timeline-item" key={item.id}>
                <span className="timeline-dot" />
                <div>
                  <strong>{item.subject}</strong>
                  <p>{item.interaction_type} · {formatDate(item.interaction_date)}</p>
                  <small>{item.sentiment}</small>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
