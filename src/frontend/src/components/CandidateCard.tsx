import React from "react";
import { LuCircleCheck, LuCircle } from "react-icons/lu";
import type { ScrapedItem } from "../types";

interface CandidateCardProps {
  candidate: ScrapedItem;
  isSelected: boolean;
  onToggle: (url: string) => void;
}

const CandidateCard: React.FC<CandidateCardProps> = ({
  candidate,
  isSelected,
  onToggle,
}) => {
  return (
    <div
      onClick={() => onToggle(candidate.url)}
      className={`p-6 rounded-2xl border-2 transition-all cursor-pointer relative group ${
        isSelected
          ? "border-blue-500 bg-blue-900/20 shadow-[0_0_20px_rgba(59,130,246,0.2)]"
          : "border-gray-800 bg-gray-900/40 hover:border-gray-600"
      }`}
    >
      <div className="absolute top-4 right-4 text-2xl z-10">
        {isSelected ? (
          <LuCircleCheck className="text-blue-500" />
        ) : (
          <LuCircle className="text-gray-600 group-hover:text-gray-400" />
        )}
      </div>
      <div className="aspect-video mb-4 rounded-xl overflow-hidden bg-gray-800/50 flex items-center justify-center border border-gray-700/50 group-hover:border-blue-500/30 transition-colors">
        {candidate.image_url ? (
          <img 
            src={candidate.image_url} 
            alt={candidate.name}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x225?text=No+Image';
            }}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-1 scale-75">
            <span className="text-3xl">📦</span>
            <span className="text-[8px] font-bold uppercase tracking-widest text-center">No Image Available</span>
          </div>
        )}
      </div>
      <h3 className="font-bold text-lg mb-2 pr-8 line-clamp-2 text-white">
        {candidate.name}
      </h3>
      <p className="text-green-400 font-mono text-xl mb-4">
        {candidate.price !== undefined
          ? typeof candidate.price === "number"
            ? `$${candidate.price.toFixed(2)}`
            : candidate.price
          : "N/A"}
      </p>
      <div className="flex items-center justify-between text-sm">
        <span className="px-2 py-1 bg-gray-800 rounded text-gray-400 italic">
          {candidate.source}
        </span>
        <span className="text-gray-500 truncate max-w-[150px]">
          {candidate.url}
        </span>
      </div>
    </div>
  );
};

export default CandidateCard;
