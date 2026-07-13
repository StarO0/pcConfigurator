"use client";

import { motion } from "framer-motion";
import { Zap } from "lucide-react";

type PowerBadgeProps = {
  watts: number;
};

function getPowerInfo(watts: number): {
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
  barFill: number;
} {
  if (watts < 350) {
    return {
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/20",
      label: "Экономичный",
      barFill: watts / 600,
    };
  } else if (watts < 500) {
    return {
      color: "text-yellow-400",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/20",
      label: "Умеренный",
      barFill: watts / 600,
    };
  } else if (watts < 650) {
    return {
      color: "text-orange-400",
      bgColor: "bg-orange-500/10",
      borderColor: "border-orange-500/20",
      label: "Высокий",
      barFill: watts / 700,
    };
  } else {
    return {
      color: "text-red-400",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/20",
      label: "Очень высокий",
      barFill: Math.min(watts / 800, 1),
    };
  }
}

export default function PowerBadge({ watts }: PowerBadgeProps) {
  const { color, bgColor, borderColor, label, barFill } = getPowerInfo(watts);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className={`rounded-xl border ${borderColor} ${bgColor} p-3.5 mt-3`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Zap className={`w-3.5 h-3.5 ${color}`} />
          <span className="text-xs font-semibold text-white/60">Энергопотребление</span>
        </div>
        <span className={`text-xs font-semibold ${color}`}>{label}</span>
      </div>

      <div className="flex items-center gap-2.5">
        {/* Bar */}
        <div className="flex-1 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${
              watts < 350
                ? "bg-emerald-400"
                : watts < 500
                ? "bg-yellow-400"
                : watts < 650
                ? "bg-orange-400"
                : "bg-red-400"
            }`}
            initial={{ width: 0 }}
            animate={{ width: `${barFill * 100}%` }}
            transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          />
        </div>
        {/* Value */}
        <span className={`text-sm font-bold tabular-nums ${color}`}>
          ~{watts}W
        </span>
      </div>

      <p className="text-[10px] text-white/30 mt-1.5">
        ≈ {((watts * 8 * 30) / 1000).toFixed(0)} кВт·ч/мес при 8ч в день
      </p>
    </motion.div>
  );
}
