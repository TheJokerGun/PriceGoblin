import React from "react";
import { LuCircleCheck, LuCircle } from "react-icons/lu";
import type { ScrapedItem } from "../types";
import { formatCurrency } from "../utils/formatters";

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
      className={`p-6 rounded-2xl border-2 transition-all cursor-pointer relative group duration-300 ${
        isSelected
          ? "border-blue-500 dark:bg-blue-900/20 bg-blue-50 shadow-[0_0_20px_rgba(59,130,246,0.2)]"
          : "dark:border-gray-800 border-gray-200 dark:bg-gray-900/40 bg-white hover:border-blue-400/50 hover:dark:border-gray-600"
      }`}
    >
      <div className="absolute top-4 right-4 text-2xl z-10 transition-colors">
        {isSelected ? (
          <LuCircleCheck className="text-blue-500" />
        ) : (
          <LuCircle className="dark:text-gray-600 text-gray-300 group-hover:dark:text-gray-400 group-hover:text-gray-500" />
        )}
      </div>
      <div className="aspect-video mb-4 rounded-xl overflow-hidden dark:bg-gray-800/50 bg-gray-50 flex items-center justify-center border dark:border-gray-700/50 border-gray-200 group-hover:border-blue-500/30 transition-colors">
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
      <h3 className="font-bold text-lg mb-2 pr-8 line-clamp-2 dark:text-white text-gray-900">
        {candidate.name}
      </h3>
      <p className="text-green-400 font-mono text-xl mb-4">
        {formatCurrency(candidate.price)}
      </p>
      <div className="flex items-center justify-between text-sm">
        <span className="px-2 py-1 dark:bg-gray-800 bg-gray-100 rounded dark:text-gray-400 text-gray-500 italic font-medium">
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
