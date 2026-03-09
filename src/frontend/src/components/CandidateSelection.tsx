import React from "react";
import { LuArrowLeft, LuRefreshCw } from "react-icons/lu";
import type { ScrapedItem } from "../types";
import CandidateCard from "./CandidateCard";

interface CandidateSelectionProps {
  candidates: ScrapedItem[];
  selectedUrls: Set<string>;
  onToggleCandidate: (url: string) => void;
  onTrackSelected: () => void;
  onBack: () => void;
  isTracking: boolean;
}

const CandidateSelection: React.FC<CandidateSelectionProps> = ({
  candidates,
  selectedUrls,
  onToggleCandidate,
  onTrackSelected,
  onBack,
  isTracking,
}) => {
  return (
    <div className="container mx-auto p-4 min-h-screen bg-black text-white">
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={onBack}
          className="p-2 hover:bg-gray-800 rounded-full transition-colors"
        >
          <LuArrowLeft size={24} />
        </button>
        <h2 className="text-3xl font-bold bg-linear-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Select Products to Track
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-20">
        {candidates.map((candidate, idx) => (
          <CandidateCard
            key={idx}
            candidate={candidate}
            isSelected={selectedUrls.has(candidate.url)}
            onToggle={onToggleCandidate}
          />
        ))}
      </div>

      <div className="fixed bottom-0 left-0 right-0 p-6 bg-linear-to-t from-black via-black/90 to-transparent flex justify-center z-50">
        <button
          onClick={onTrackSelected}
          disabled={isTracking || selectedUrls.size === 0}
          className={`
            flex items-center gap-3 px-12 py-4 rounded-full font-bold text-lg transition-all
            ${
              isTracking || selectedUrls.size === 0
                ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-500 text-white shadow-xl hover:scale-105 active:scale-95 shadow-blue-500/10"
            }
          `}
        >
          {isTracking ? (
            <>
              <LuRefreshCw className="animate-spin" /> Tracking...
            </>
          ) : (
            `Track ${selectedUrls.size} Selected Items`
          )}
        </button>
      </div>
    </div>
  );
};

export default CandidateSelection;
