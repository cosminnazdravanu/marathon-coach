// src/components/WorkoutModal.jsx
import { useEffect, useState, useRef } from "react";
import Draggable from "react-draggable";
import { ResizableBox } from "react-resizable";
import "react-resizable/css/styles.css";
import { motion, AnimatePresence } from "framer-motion";
import { getLabelForDate } from "../../utils/dateHelpers";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const isMobile = () => window.innerWidth < 768;

async function csrf() {
  const r = await fetch(`${API}/auth/csrf`, { credentials: "include" });
  const j = await r.json();
  return j.csrf;
}

export default function WorkoutModal({
  visible,
  onClose,
  date,
  editingWorkout,
  onSaveSuccess,
  containerRef,
}) {
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const dragRef = useRef(null);
  const backdropRef = useRef(null);

  const [size, setSize] = useState(() => {
    const saved = localStorage.getItem("modalSize");
    return saved ? JSON.parse(saved) : { width: 400, height: 300 };
  });
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const prevSizeRef = useRef(size);

  // ESC to close
  useEffect(() => {
    const handler = (e) => e.key === "Escape" && onClose();
    if (visible) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [visible, onClose]);

  // Center in container on open + hydrate fields
  useEffect(() => {
    if (visible) {
      setDescription(editingWorkout?.description || "");
      if (containerRef?.current && !isMobile()) {
        const { left, top, width, height } =
          containerRef.current.getBoundingClientRect();
        const x = left + (width - size.width) / 2;
        const y = top + (height - size.height) / 2;
        setPosition({ x, y });
      } else {
        // mobile: let it stick to the viewport center
        setPosition({ x: 0, y: 0 });
      }
    }
  }, [visible, containerRef, editingWorkout, size]);

  async function handleSave() {
    if (!description.trim()) return;
    setSubmitting(true);
    try {
      const payload = {
        date,
        type: "planned",
        description: description.trim(),
        warmup_target: null,
        main_target: null,
        cooldown_target: null,
        terrain: null,
        notes: null,
      };

      const base = `${API}/plans`;
      const url = editingWorkout?.id ? `${base}/${editingWorkout.id}` : base;
      const method = editingWorkout?.id ? "PUT" : "POST";

      const token = await csrf();
      const res = await fetch(url, {
        method,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": token,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(await res.text());

      onClose();
      onSaveSuccess && onSaveSuccess();
    } catch (e) {
      console.error(e);
      alert("Failed to save workout.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!editingWorkout?.id) return;
    if (!confirm("Delete this workout?")) return;

    setSubmitting(true);
    try {
      const token = await csrf();
      const res = await fetch(`${API}/plans/${editingWorkout.id}`, {
        method: "DELETE",
        credentials: "include",
        headers: { "X-CSRF-Token": token },
      });
      if (!res.ok) throw new Error(await res.text());

      onClose();
      onSaveSuccess && onSaveSuccess();
    } catch (e) {
      console.error(e);
      alert("Failed to delete workout.");
    } finally {
      setSubmitting(false);
    }
  }

  const onResizeStop = (_, data) => {
    setSize(data.size);
    localStorage.setItem("modalSize", JSON.stringify(data.size));
  };

  const onResize = (_, { size: newSize, handle }) => {
    const { width: oldW, height: oldH } = prevSizeRef.current;
    const deltaW = newSize.width - oldW;
    const deltaH = newSize.height - oldH;
    let { x, y } = position;

    if (handle.includes("w")) x -= deltaW; // resizing from left
    if (handle.includes("n")) y -= deltaH; // resizing from top

    setPosition({ x, y });
    setSize(newSize);
    prevSizeRef.current = newSize;
  };

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="fixed inset-0 bg-black/50 z-50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {/* Invisible overlay to catch outside clicks */}
          <div
            ref={backdropRef}
            className="absolute inset-0"
            onClick={() => !submitting && onClose()}
            style={{ zIndex: 0 }}
          />

          {/* Modal box wrapper */}
          <Draggable
            nodeRef={dragRef}
            handle=".modal-header"
            disabled={isMobile()}
            position={position}
            onStop={(_, data) => setPosition({ x: data.x, y: data.y })}
          >
            <div ref={dragRef} style={{ zIndex: 10, position: "absolute" }}>
              <motion.div
                onClick={(e) => e.stopPropagation()}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {/* wrap in a form so Enter will submit */}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!submitting) handleSave();
                  }}
                >
                  <ResizableBox
                    width={size.width}
                    height={size.height}
                    minConstraints={[300, 200]}
                    maxConstraints={[800, 800]}
                    resizeHandles={
                      isMobile() ? [] : ["se", "e", "s", "n", "w", "ne", "nw", "sw"]
                    }
                    onResize={onResize}
                    onResizeStop={onResizeStop}
                    className="bg-white rounded-2xl shadow-xl p-6 flex flex-col overflow-hidden"
                  >
                    <div className="modal-header cursor-move mb-4">
                      <h3 className="text-lg font-semibold">
                        {editingWorkout ? "Edit" : "New"} Workout –{" "}
                        {getLabelForDate(date)}
                      </h3>
                    </div>

                    <label className="sr-only" htmlFor="workout-desc">
                      Workout description
                    </label>
                    <input
                      id="workout-desc"
                      type="text"
                      placeholder="Planned Workout"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4"
                      autoFocus
                      required
                      maxLength={150}
                      disabled={submitting}
                    />

                    <div className="flex justify-between mt-auto">
                      {editingWorkout && (
                        <button
                          type="button"
                          onClick={handleDelete}
                          disabled={submitting}
                          className="px-4 py-2 rounded-lg bg-red-100 text-red-600 hover:bg-red-200 disabled:opacity-60"
                        >
                          Delete
                        </button>
                      )}
                      <div className="flex gap-2 ml-auto">
                        <button
                          type="button"
                          onClick={onClose}
                          disabled={submitting}
                          className="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 disabled:opacity-60"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submitting}
                          className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
                        >
                          {submitting ? "Saving…" : "Save"}
                        </button>
                      </div>
                    </div>
                  </ResizableBox>
                </form>
              </motion.div>
            </div>
          </Draggable>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
