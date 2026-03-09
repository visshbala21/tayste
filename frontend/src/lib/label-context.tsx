"use client";

import { createContext, useContext } from "react";

type LabelContextValue = {
  activeLabelId: string | null;
};

const LabelContext = createContext<LabelContextValue>({ activeLabelId: null });

export function LabelProvider({
  activeLabelId,
  children,
}: {
  activeLabelId: string | null;
  children: React.ReactNode;
}) {
  return (
    <LabelContext.Provider value={{ activeLabelId }}>
      {children}
    </LabelContext.Provider>
  );
}

export function useActiveLabel() {
  return useContext(LabelContext);
}
