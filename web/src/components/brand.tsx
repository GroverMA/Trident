export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className={compact ? "brand brandCompact" : "brand"}>
      <div className="brandName">Trident</div>
      <div className="brandSlogan">
        Dive Deep into Industries.
        <br />
        Surface with Direction.
      </div>
      <div className="brandSub">Enterprise research &amp; strategic decision intelligence</div>
    </div>
  );
}
