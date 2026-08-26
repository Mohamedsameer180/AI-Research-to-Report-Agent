import React from 'react'

export default function AiCore({ status = 'Verifying evidence...', isWorking = true }) {
  return (
    <div className="flex flex-col items-center justify-center p-4">
      {/* Reactor Centerpiece */}
      <div className="relative w-36 h-36 flex items-center justify-center">
        {/* Outer Laser Dashed Ring */}
        <div className={`absolute inset-0 rounded-full border border-dashed border-[#FF6A00]/40 ${isWorking ? 'animate-spin-slow' : 'opacity-40'}`} />
        
        {/* Secondary Counter-Rotating Ring */}
        <div 
          className={`absolute inset-3 rounded-full border border-[#FF8A00]/30 border-t-[#FF6A00] border-b-[#FF8A00] ${isWorking ? 'animate-spin-reverse-slow' : 'opacity-30'}`}
          style={{ animationDuration: '10s' }}
        />

        {/* Orbiting Particle Beacons */}
        {isWorking && (
          <>
            <div className="absolute w-2 h-2 rounded-full bg-[#FF8A00] shadow-[0_0_8px_#FF8A00] animate-spin" style={{ animationDuration: '4s', top: '2px', left: 'calc(50% - 4px)', transformOrigin: '4px 68px' }} />
            <div className="absolute w-1.5 h-1.5 rounded-full bg-[#FF6A00] shadow-[0_0_6px_#FF6A00] animate-spin" style={{ animationDuration: '6s', animationDirection: 'reverse', bottom: '6px', left: 'calc(50% - 3px)', transformOrigin: '3px -60px' }} />
          </>
        )}

        {/* Inner Segment Ring */}
        <div className="absolute inset-7 rounded-full border border-white/10 border-r-[#FF6A00]/60 border-l-white/20" />

        {/* Core Glowing Orb */}
        <div className={`absolute w-16 h-16 rounded-full bg-gradient-to-tr from-[#FF6A00]/20 via-[#FF8A00]/40 to-[#FF6A00]/10 flex flex-col items-center justify-center backdrop-blur-sm border border-[#FF6A00]/50 shadow-[0_0_25px_rgba(255,106,0,0.35)] ${isWorking ? 'animate-pulse-glow' : ''}`}>
          <span className="text-[11px] font-extrabold tracking-widest text-[#FF8A00] leading-none">AI</span>
          <span className="text-[8px] font-semibold tracking-wider text-white/90 uppercase mt-0.5 leading-none">
            {isWorking ? 'WORKING' : 'IDLE'}
          </span>
        </div>
      </div>

      {/* Dynamic Status Text */}
      <div className="mt-3 text-center">
        <div className="flex items-center justify-center gap-1.5 text-xs text-[#A1A1AA]">
          <span className={`w-1.5 h-1.5 rounded-full ${isWorking ? 'bg-[#FF6A00] animate-ping' : 'bg-zinc-600'}`} />
          <span className="font-mono text-zinc-300 tracking-wide text-[11px] max-w-[200px] truncate">
            {status}
          </span>
        </div>
      </div>
    </div>
  )
}
