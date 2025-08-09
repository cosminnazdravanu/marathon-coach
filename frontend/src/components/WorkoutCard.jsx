// src/components/WorkoutCard.jsx
import React, { useState, useCallback } from "react";
import clsx from "clsx";
import { FaRunning, FaDumbbell } from "react-icons/fa";
import { FiMoreVertical } from "react-icons/fi";

export default React.memo(function WorkoutCard({ workout, onEdit }) {
  const [isDragging, setIsDragging] = useState(false);

  const isPlanned = workout?.type === "planned";
  const canEdit = Boolean(onEdit && isPlanned); // edit/move only planned items
  const icon = isPlanned ? (
    <FaRunning className="text-blue-500 shrink-0 mt-0.5" aria-hidden />
  ) : (
    <FaDumbbell className="text-green-500 shrink-0 mt-0.5" aria-hidden />
  );

  const description =
    workout?.description?.trim() ||
    (isPlanned ? "Planned workout" : "Imported activity");

  const handleDragStart = useCallback(
    (e) => {
      if (!isPlanned) return; // no dragging for Strava items
      setIsDragging(true);
      e.dataTransfer.setData(
        "application/json",
        JSON.stringify({ id: workout.id, date: workout.date })
      );
      e.dataTransfer.effectAllowed = "move";
    },
    [isPlanned, workout?.id, workout?.date]
  );

  const handleDragEnd = useCallback(() => setIsDragging(false), []);
  const handleEditClick = useCallback(() => {
    if (canEdit) onEdit(workout);
  }, [canEdit, onEdit, workout]);

  const handleKeyDown = useCallback(
    (e) => {
      if (!canEdit) return;
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onEdit(workout);
      }
    },
    [canEdit, onEdit, workout]
  );

  return (
    <div
      draggable={isPlanned}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      aria-grabbed={isDragging || undefined}
      title={description}
      className={clsx(
        "bg-white shadow rounded-lg p-2 flex justify-between items-start transition-all duration-150 select-none",
        "hover:shadow hover:bg-gray-50",
        isPlanned ? "border-l-4 border-blue-500" : "border-l-4 border-green-500",
        {
          "cursor-grab": isPlanned,
          "opacity-70 scale-95": isDragging,
          "opacity-100 scale-100": !isDragging,
        }
      )}
    >
      <div className="flex items-start gap-2 min-w-0">
        {icon}
        <div className="flex flex-col min-w-0">
          <span className="text-sm font-medium text-gray-800 truncate">
            {description}
          </span>
          {/* Optional extras if present */}
          {workout.distance ? (
            <span className="text-xs text-gray-500">{workout.distance}</span>
          ) : null}
          {workout.notes ? (
            <span className="text-xs text-gray-500 truncate">{workout.notes}</span>
          ) : null}
        </div>
      </div>

      {canEdit && (
        <button
          type="button"
          onClick={handleEditClick}
          onKeyDown={handleKeyDown}
          className="text-gray-400 hover:text-gray-600 p-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Edit workout"
        >
          <FiMoreVertical />
        </button>
      )}
    </div>
  );
});
