import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import AppLayout from "../layouts/AppLayout";

import DraftPanel from "../components/draft/DraftPanel";
import InteractionForm from "../components/interaction/InteractionForm";
import AIChatPanel from "../components/chat/AIChatPanel";
import CRMInsights from "../components/insights/CRMInsights";

import LoadingOverlay from "../components/common/LoadingOverlay";
import Toast from "../components/common/Toast";

import useChat from "../hooks/useChat";
import { hideToast } from "../store";

import "../styles/InteractionPage.css";

export default function InteractionPage() {
  const dispatch = useDispatch();

  const {
    loading,
    toast,
  } = useSelector((state) => state.crm);

  const chat = useChat();

  useEffect(() => {
    if (!toast.open) return;

    const timer = setTimeout(() => {
      dispatch(hideToast());
    }, 3500);

    return () => clearTimeout(timer);
  }, [toast.open, dispatch]);

  const leftPanel = (
    <div className="review-workspace">
      <DraftPanel />

      <InteractionForm />

      <CRMInsights />
    </div>
  );

  const rightPanel = <AIChatPanel {...chat} />;

  return (
    <>
      {loading && <LoadingOverlay />}

      {toast.open && <Toast {...toast} />}

      <AppLayout
        left={leftPanel}
        right={rightPanel}
      />
    </>
  );
}