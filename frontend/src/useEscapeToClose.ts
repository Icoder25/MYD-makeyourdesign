import { useEffect } from "react";

/** Close an open overlay when Escape is pressed.
 *
 * Every modal here could already be dismissed by clicking the backdrop or the
 * ✕, which leaves anyone working from the keyboard with no way out of a
 * dialog. The listener only exists while the overlay is open, so a stack of
 * modals closes the topmost one first.
 */
export function useEscapeToClose(isOpen: boolean, onClose: () => void): void {
  useEffect(() => {
    if (!isOpen) return;

    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    };

    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);
}
