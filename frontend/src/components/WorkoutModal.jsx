import { useEffect, useState, useRef } from "react";
import Draggable from "react-draggable";
import { ResizableBox } from "react-resizable";
import "react-resizable/css/styles.css";
import { motion, AnimatePresence } from "framer-motion";
import { getLabelForDate } from "../../utils/dateHelpers";

const isMobile = () => window.innerWidth < 768;

export default function WorkoutModal({
  visible,
  onClose,
  date,
  editingWorkout,
  onSaveSuccess,
  containerRef,
}) {
  const [description, setDescription] = useState("");
  const dragRef = useRef(null);
  const backdropRef = useRef(null);
  const [size, setSize] = useState({ width: 400, height: 300 });
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const prevSizeRef = useRef(size);
  const API = import.meta.env.VITE_API_URL || ""; 

  // ESC to close
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") onClose();
    };
    if (visible) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [visible]);

  // Center in container on open
  useEffect(() => {
    if (visible && containerRef?.current && !isMobile()) {
      const { left, top, width, height } = containerRef.current.getBoundingClientRect();
      const x = left + (width  - size.width ) / 2;
      const y = top  + (height - size.height) / 2;
      setPosition({ x, y });
    }
    if (visible) {
      setDescription(editingWorkout?.description || "");
    }
  }, [visible, containerRef, editingWorkout, size]);

  const handleSave = async () => {
    const payload = {
      date,
      type: "planned",
      description,
      warmup_target: null,
      main_target: null,
      cooldown_target: null,
      terrain: null,
      notes: null,
    };

    const base = `${API}/plans`;
    const url  = editingWorkout?.id ? `${base}/${editingWorkout.id}` : base;
    const method = editingWorkout?.id ? "PUT"   : "POST";

    await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    onClose();
    if (onSaveSuccess) onSaveSuccess();
  };

  const handleDelete = async () => {
    if (!editingWorkout?.id) return;

    await fetch(`${API}/plans/${editingWorkout.id}`, {
      method: "DELETE",
    });

    onClose();
    if (onSaveSuccess) onSaveSuccess();
  };

  const onResizeStop = (_, data) => {
    setSize(data.size);
    localStorage.setItem("modalSize", JSON.stringify(data.size));
  };

  const onResize = (_, { size: newSize, handle }) => {
    const { width: oldW, height: oldH } = prevSizeRef.current;
    const deltaW = newSize.width  - oldW;
    const deltaH = newSize.height - oldH;
    let { x, y } = position;

    // if resizing from the left, shift x right by the width gain
    if (handle.includes("w")) x -= deltaW;
    // if resizing from the top, shift y down by the height gain
    if (handle.includes("n")) y -= deltaH;

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
            onClick={onClose}
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
                  onSubmit={e => {
                    e.preventDefault();       // don’t reload the page
                    handleSave();             // save + close
                  }}
                >
                  <ResizableBox
                    width={size.width}
                    height={size.height}
                    minConstraints={[300, 200]}
                    maxConstraints={[800, 800]}
                    resizeHandles={
                      isMobile()
                        ? []
                        : ["se", "e", "s", "n", "w", "ne", "nw", "sw"]
                    }
                    onResize={onResize}
                    onResizeStop={onResizeStop}
                    className="bg-white rounded-2xl shadow-xl p-6 flex flex-col overflow-hidden"
                  >
                    <div className="modal-header cursor-move mb-4">
                      <h3 className="text-lg font-semibold">
                        {editingWorkout ? "Edit" : "New"} Workout – {getLabelForDate(date)}
                      </h3>
                    </div>
                    <input
                      type="text"
                      placeholder="Planned Workout"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 mb-4"
                      autoFocus
                      required
                      maxLength={150} //trebuie sa vad cat e in baza de date
                    />
                    <div className="flex justify-between mt-auto">
                      {editingWorkout && (
                        <button
                          type="button"
                          onClick={handleDelete}
                          className="px-4 py-2 rounded-lg bg-red-100 text-red-600 hover:bg-red-200"
                        >
                          Delete
                        </button>
                      )}
                      <div className="flex gap-2 ml-auto">
                        <button
                          type="button"
                          onClick={onClose}
                          className="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
                        >
                          Save
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
