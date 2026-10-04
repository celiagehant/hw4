/**
 * "Dan", the chat assistant's avatar: a friendly bulldog face inspired by
 * Handsome Dan, Yale's mascot. Drawn as an original SVG (not a Yale logo).
 */
export default function DanAvatar({ size = 40, title }: { size?: number; title?: string }) {
  return (
    <svg
      className="dan-avatar"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role={title ? "img" : undefined}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      <circle cx="32" cy="32" r="32" fill="#00356b" />
      {/* ears */}
      <path d="M12 20c2-7 9-9 13-6-2 4-5 8-9 11-3-1-4-3-4-5z" fill="#d8cfbf" />
      <path d="M52 20c-2-7-9-9-13-6 2 4 5 8 9 11 3-1 4-3 4-5z" fill="#d8cfbf" />
      {/* head */}
      <path
        d="M14 34c0-11 8-18 18-18s18 7 18 18c0 4-1 8-3 11-3 6-9 9-15 9s-12-3-15-9c-2-3-3-7-3-11z"
        fill="#f7f3ea"
      />
      {/* brow wrinkles */}
      <path d="M25 24c4-2 10-2 14 0" stroke="#cbbfa9" strokeWidth="1.6" fill="none" strokeLinecap="round" />
      <path d="M27 27.5c3-1.2 7-1.2 10 0" stroke="#cbbfa9" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      {/* eyes */}
      <circle cx="24.5" cy="32" r="2.6" fill="#0f1b2d" />
      <circle cx="39.5" cy="32" r="2.6" fill="#0f1b2d" />
      <circle cx="25.4" cy="31.1" r="0.8" fill="#fff" />
      <circle cx="40.4" cy="31.1" r="0.8" fill="#fff" />
      {/* jowls / muzzle */}
      <path d="M20 42c0-5 5-8 12-8s12 3 12 8c0 5-5 8-12 8s-12-3-12-8z" fill="#ffffff" />
      {/* nose */}
      <path d="M27.5 37.2c0-1.6 2-2.6 4.5-2.6s4.5 1 4.5 2.6c0 1.8-2.4 3.4-4.5 3.4s-4.5-1.6-4.5-3.4z" fill="#0f1b2d" />
      {/* mouth + underbite */}
      <path d="M32 40.6v2.4M32 43c-2 2.2-5 2.4-7 1M32 43c2 2.2 5 2.4 7 1" stroke="#0f1b2d" strokeWidth="1.4" fill="none" strokeLinecap="round" />
      <path d="M28.6 45.4l1-1.6 1 1.6zM33.4 45.4l1-1.6 1 1.6z" fill="#ffffff" stroke="#cbbfa9" strokeWidth="0.4" />
      {/* collar */}
      <path d="M20 53c3 3 7.5 4.5 12 4.5s9-1.5 12-4.5" stroke="#c9a227" strokeWidth="3" fill="none" strokeLinecap="round" />
      <circle cx="32" cy="58" r="2.2" fill="#c9a227" />
    </svg>
  );
}
