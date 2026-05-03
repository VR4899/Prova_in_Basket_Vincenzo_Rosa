import { useId } from "react";

export default function FiscoFacileLogo({
  size = 96,
  color = "#CCFF00",
  textColor = "#FAFAFA",
  showRotation = false,
}) {
  const id = useId();

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 200 200"
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: "block" }}
    >
      <defs>
        <radialGradient id={`${id}-bg`} cx="50%" cy="42%" r="62%">
          <stop offset="0%" stopColor="#1b1b1f" />
          <stop offset="100%" stopColor="#09090b" />
        </radialGradient>

        <clipPath id={`${id}-clip`}>
          <circle cx="100" cy="102" r="40" />
        </clipPath>

        {/* 🔥 PATH CIRCOLARE PER TESTO */}
        <path
          id={`${id}-circle-text`}
          d="
            M 100,100
            m -63,0
            a 63,63 0 1,1 126,0
            a 63,63 0 1,1 -126,0
          "
        />
      </defs>

      {/* sfondo */}
      <circle
        cx="100"
        cy="100"
        r="90"
        fill={`url(#${id}-bg)`}
        stroke={color}
        strokeWidth="2.2"
      />
      <circle
        cx="100"
        cy="100"
        r="79"
        fill="none"
        stroke={color}
        strokeOpacity="0.26"
        strokeWidth="1.6"
      />

      {/* linee radiali */}
      {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
        const rad = (deg * Math.PI) / 180;
        return (
          <line
            key={deg}
            x1={100 + Math.cos(rad) * 83}
            y1={100 + Math.sin(rad) * 83}
            x2={100 + Math.cos(rad) * 88}
            y2={100 + Math.sin(rad) * 88}
            stroke={color}
            strokeWidth="1.5"
            strokeOpacity="0.72"
          />
        );
      })}

      {/* 🔥 TESTO CURVO */}
      <g
        style={
          showRotation
            ? {
                animation: "ff-rotate 24s linear infinite",
                transformOrigin: "100px 100px",
              }
            : {}
        }
      >
        {/* TOP */}
        <text
          fill={textColor}
          fontFamily="Outfit, system-ui, sans-serif"
          fontSize="12"
          fontWeight="900"
          letterSpacing="3.2"
        >
          <textPath
            href={`#${id}-circle-text`}
            startOffset="25%"
            textAnchor="middle"
          >
            FISCO FACILE
          </textPath>
        </text>

        {/* BOTTOM */}
        <text
          fill={color}
          fontFamily="Outfit, system-ui, sans-serif"
          fontSize="7"
          fontWeight="700"
          letterSpacing="2.8"
          opacity="0.88"
        >
          <textPath
            href={`#${id}-circle-text`}
            startOffset="75%"
            textAnchor="middle"
          >
            GUIDE FISCALI DIGITALI
          </textPath>
        </text>
      </g>

      {/* centro */}
      <circle
        cx="100"
        cy="102"
        r="46"
        fill="none"
        stroke={color}
        strokeOpacity="0.24"
        strokeWidth="2"
      />

      <g clipPath={`url(#${id}-clip)`}>
        <circle
          cx="100"
          cy="102"
          r="40"
          fill={color}
          fillOpacity="0.05"
          stroke={color}
          strokeWidth="2.6"
        />

        <ellipse
          cx="100"
          cy="102"
          rx="21"
          ry="40"
          fill="none"
          stroke={color}
          strokeOpacity="0.54"
          strokeWidth="1.8"
        />
        <ellipse
          cx="100"
          cy="102"
          rx="8"
          ry="40"
          fill="none"
          stroke={color}
          strokeOpacity="0.28"
          strokeWidth="1.6"
        />
        <ellipse
          cx="100"
          cy="102"
          rx="40"
          ry="22"
          fill="none"
          stroke={color}
          strokeOpacity="0.48"
          strokeWidth="1.8"
        />
        <ellipse
          cx="100"
          cy="102"
          rx="40"
          ry="9"
          fill="none"
          stroke={color}
          strokeOpacity="0.24"
          strokeWidth="1.6"
        />

        <text
          x="100"
          y="116"
          textAnchor="middle"
          fill={color}
          fontFamily="Outfit, system-ui, sans-serif"
          fontSize="45"
          fontWeight="900"
        >
          €
        </text>
      </g>

      <style>{`
        @keyframes ff-rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </svg>
  );
}