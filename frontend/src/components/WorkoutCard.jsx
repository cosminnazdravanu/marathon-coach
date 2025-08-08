// src/components/WorkoutCard.jsx
import React, { useState, useCallback } from 'react';
import clsx from 'clsx';
import { FaRunning, FaDumbbell } from 'react-icons/fa';
import { FiMoreVertical } from 'react-icons/fi';

export default React.memo(function WorkoutCard({ workout, onEdit }) {
  const [isDragging, setIsDragging] = useState(false);
  const isPlanned = workout.type === 'planned';
  const icon = isPlanned
    ? <FaRunning className="text-blue-500" />
    : <FaDumbbell className="text-green-500" />;

  const handleDragStart = useCallback(e => {
    setIsDragging(true);
    e.dataTransfer.setData(
      'application/json',
      JSON.stringify({ id: workout.id, date: workout.date })
    );
    e.dataTransfer.effectAllowed = 'move';
  }, [workout.id, workout.date]);

  const handleDragEnd = useCallback(() => setIsDragging(false), []);
  const handleEditClick = useCallback(() => onEdit && onEdit(workout), [onEdit, workout]);

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      className={clsx(
        'bg-white shadow rounded-lg p-2 flex justify-between items-start cursor-grab transition-all duration-150',
        'hover:shadow hover:bg-gray-100 hover:scale-[1.001]',
        { 'opacity-70 scale-95': isDragging, 'opacity-100 scale-100': !isDragging }
      )}
    >
      <div className="flex items-start space-x-2">
        {icon}
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-800">{workout.description}</span>
          {workout.distance && <span className="text-xs text-gray-500">{workout.distance}</span>}
        </div>
      </div>
      {onEdit && (
        <button onClick={handleEditClick} className="text-gray-400 hover:text-gray-600">
          <FiMoreVertical />
        </button>
      )}
    </div>
  );
});
