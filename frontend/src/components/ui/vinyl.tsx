type VinylProps = {
  size?: number;
  className?: string;
  imageUrl?: string;
};

export function Vinyl({ size = 90, className = "", imageUrl }: VinylProps) {
  const innerSize = Math.round(size * 0.2);

  if (imageUrl) {
    return (
      <div
        className={`rounded-full flex-shrink-0 overflow-hidden border-2 border-white/[0.12] shadow-[0_0_30px_rgba(124,92,252,0.25)] ${className}`}
        style={{ width: size, height: size }}
      >
        <img
          src={imageUrl}
          alt=""
          className="w-full h-full object-cover"
        />
      </div>
    );
  }

  return (
    <div
      className={`vinyl ${className}`}
      style={{ width: size, height: size }}
    >
      <div
        className="rounded-full bg-[#0a0a0a] border-2 border-white/[0.12]"
        style={{ width: innerSize, height: innerSize, position: "absolute" }}
      />
    </div>
  );
}
