const EMAIL_RE = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

export function isValidEmail(value: string): boolean {
  return EMAIL_RE.test(value);
}

export function isValidUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

export function validateLinkOrEmail(value: string): string | true {
  if (!value) return true;
  return isValidEmail(value) || isValidUrl(value)
    ? true
    : "Enter a valid URL (starting with http:// or https://) or an email address";
}

export function toHref(value: string): string {
  return isValidEmail(value) ? `mailto:${value}` : value;
}
