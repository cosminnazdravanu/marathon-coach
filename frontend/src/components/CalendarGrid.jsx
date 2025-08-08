// src/components/CalendarGrid.jsx
import React, { useState, useEffect, useRef, useLayoutEffect, useCallback, useMemo } from 'react';
import clsx from 'clsx';
import throttle from 'lodash.throttle';
import { addDays, subDays, format, eachDayOfInterval, startOfMonth, endOfMonth, startOfWeek, addMonths, subMonths } from 'date-fns';
import { FiPlus, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import WorkoutModal from './WorkoutModal';
import WorkoutCard from './WorkoutCard';
import { getLabelForDate } from '../../utils/dateHelpers';
import { Popover, PopoverButton, PopoverPanel, Transition } from '@headlessui/react'
import { CalendarIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

// Generate a continuous range of dates centered around `centerDate`
function generateDates(centerDate, weeksBack, weeksForward) {
  const now = new Date(centerDate);
  const offset = (now.getDay() + 6) % 7; // Monday = 0
  const monday = subDays(now, offset);
  const start = subDays(monday, weeksBack * 7);
  const totalDays = (weeksBack + weeksForward + 1) * 7;
  return Array.from({ length: totalDays }, (_, i) => addDays(start, i));
}

export default function CalendarGrid({ weeksBack = 5, weeksForward = 5 }) {
  // State
  const [trainingPlan, setTrainingPlan] = useState({});
  const [dates, setDates] = useState([]);
  const [centerDate, setCenterDate] = useState(new Date());
  const [pickerValue, setPickerValue] = useState(new Date().toISOString().slice(0,10));
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [editingWorkout, setEditingWorkout] = useState(null);
  const [dragOverDate, setDragOverDate] = useState(null);

  // Refs
  const calendarRef = useRef(null);
  const initialScrollDone = useRef(false);

  console.log("API URL =", import.meta.env.VITE_API_URL);
  console.log("Full fetch URL =", import.meta.env.VITE_API_URL + "/plans");

  // Fetch workouts
  const loadTrainingPlan = useCallback(() => {
    fetch(import.meta.env.VITE_API_URL + '/plans')
      .then(res => res.json())
      .then(data => {
        const all = Object.values(data).flat();
        const grouped = data.reduce((acc, e) => {
          const date = e.date;
          const t = e.type || 'planned';   // <-- default it
          if (!acc[date]) acc[date] = { planned: [], strava: null };
          if (t === 'planned') acc[date].planned.push(e);
          else if (t === 'strava') acc[date].strava = e;
          return acc;
        }, {});
        setTrainingPlan(grouped);
      })
      .catch(console.error);
  }, []);
  useEffect(() => loadTrainingPlan(), [loadTrainingPlan]);

  // Compute dates around centerDate
  const initialDates = useMemo(
    () => generateDates(centerDate, weeksBack, weeksForward),
    [centerDate, weeksBack, weeksForward]
  );
  useEffect(() => {
    setDates(initialDates);
    // After setting dates, scroll to center
    const iso = centerDate.toISOString().slice(0,10);
    setTimeout(() => scrollToDate(iso), 0);
  }, [initialDates, centerDate]);
  useLayoutEffect(() => {
    if (initialScrollDone.current || dates.length === 0) return;
    const c = calendarRef.current;
    if (c) c.scrollTop = (c.scrollHeight - c.clientHeight) / 2;
    initialScrollDone.current = true;
  }, [dates]);

  // Scroll helper
  const scrollToDate = useCallback(iso => {
    const c = calendarRef.current;
    if (!c) return;
    const el = c.querySelector(`[data-date="${iso}"]`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  // Navigation handlers
  const handleToday = () => {
    setCenterDate(new Date());
    setPickerValue(new Date().toISOString().slice(0,10));
  };
  const handlePrevWeek = () => setCenterDate(subDays(centerDate, 7));
  const handleNextWeek = () => setCenterDate(addDays(centerDate, 7));

  // date picker selection triggers reload around chosen date
  const handleDateChange = useCallback(e => {
    const val = e.target.value;
    setPickerValue(val);
    if (val.length === 10) setCenterDate(new Date(val));
  }, []);

  // Date picker blur only triggers navigation
  const handleDatePickerBlur = () => {
    if (pickerValue.length === 10) {
      const sel = new Date(pickerValue);
      if (sel < dates[0] || sel > dates[dates.length - 1]) {
        setCenterDate(sel);
      } else {
        scrollToDate(pickerValue);
      }
    }
  };

  // Add/Edit handlers
  const handleAdd = useCallback(d => { setSelectedDate(d); setEditingWorkout(null); setModalVisible(true); }, []);
  const handleEdit = useCallback(w => { setSelectedDate(w.date); setEditingWorkout(w); setModalVisible(true); }, []);

  // Infinite scroll
  const scrollHandlerRef = useRef(null);
  if (!scrollHandlerRef.current) {
    scrollHandlerRef.current = throttle(() => {
      const c = calendarRef.current;
      if (!c) return;
      const { scrollTop, scrollHeight, clientHeight } = c;
      const threshold = clientHeight / 4;
      if (scrollTop < threshold) {
        const oldH = c.scrollHeight;
        setDates(prev => {
          const first = prev[0];
          const newWeek = Array.from({ length: 7 }, (_, i) => subDays(first, 7 - i));
          return [...newWeek, ...prev];
        });
        requestAnimationFrame(() => { c.scrollTop = scrollTop + (c.scrollHeight - oldH); });
      } else if (scrollTop + clientHeight > scrollHeight - threshold) {
        setDates(prev => {
          const last = prev[prev.length - 1];
          const newWeek = Array.from({ length: 7 }, (_, i) => addDays(last, i + 1));
          return [...prev, ...newWeek];
        });
      }
    }, 200);
  }
  useEffect(() => () => scrollHandlerRef.current.cancel && scrollHandlerRef.current.cancel(), []);

  // **NEW**: handle drop → update DB + reload
  const moveWorkout = useCallback((id, fromDate, toDate) => {
    fetch(`${import.meta.env.VITE_API_URL}/plans/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: toDate }),
    })
    .then(res => {
      if (!res.ok) throw new Error('Failed to move workout');
      return res.json();
    })
    .then(() => {
      loadTrainingPlan();       // re-load so UI reflects the new dates
    })
    .catch(console.error);
  }, [loadTrainingPlan]);

  return (
    <div className="w-full mx-auto py-4">
      {/* Header */}
      <div className="flex items-center justify-center space-x-2 mb-4">
        {/* date picker popover */}
        <Popover className="relative">
          {({ open, close }) => (
            <>
              <PopoverButton
                className={clsx(
                  "flex items-center px-3 py-2 rounded-md",
                  "bg-gray-50 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500",
                  open ? "ring-2 ring-blue-500" : ""
                )}
              >
                <CalendarIcon className="w-5 h-5 mr-2 text-gray-600" />
                <span className="font-medium text-gray-700">{format(new Date(pickerValue), 'MMMM yyyy')}</span>
                <ChevronDownIcon className={clsx("w-4 h-4 ml-2 transition-transform", { "rotate-180": open })} />
              </PopoverButton>

              <Transition
                as={React.Fragment}
                enter="transition ease-out duration-200"
                enterFrom="opacity-0 translate-y-1"
                enterTo="opacity-100 translate-y-0"
                leave="transition ease-in duration-150"
                leaveFrom="opacity-100 translate-y-0"
                leaveTo="opacity-0 translate-y-1"
              >
                <PopoverPanel className="absolute z-10 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg p-4 w-[300px]">
                  {/* Month & Year Selectors */}
                  <div className="flex items-center justify-between mb-4">
                    <button
                      onClick={() => setPickerValue(format(subMonths(new Date(pickerValue), 1), 'yyyy-MM-dd'))}
                      className="p-2 rounded-full hover:bg-gray-100 focus:outline-none"
                    >
                      <FiChevronLeft className="w-5 h-5 text-gray-600" />
                    </button>
                    <div className="flex space-x-2">
                      <select
                        value={format(new Date(pickerValue), 'M')}
                        onChange={e => {
                          const nm = Number(e.target.value) - 1;
                          const bd = new Date(pickerValue);
                          const c  = new Date(bd.getFullYear(), nm, 1);
                          setPickerValue(format(c, 'yyyy-MM-dd'));
                        }}
                        className="px-2 py-1 rounded-md hover:bg-gray-100 focus:ring-1 focus:ring-blue-500"
                      >
                        {Array.from({ length: 12 }, (_, i) => {
                          const m = new Date(0, i).toLocaleString('default', { month: 'short' });
                          return <option key={i} value={i+1}>{m}</option>;
                        })}
                      </select>
                      <select
                        value={format(new Date(pickerValue), 'yyyy')}
                        onChange={e => {
                          const ny = Number(e.target.value);
                          const bd = new Date(pickerValue);
                          const c  = new Date(ny, bd.getMonth(), 1);
                          setPickerValue(format(c, 'yyyy-MM-dd'));
                        }}
                        className="px-2 py-1 rounded-md hover:bg-gray-100 focus:ring-1 focus:ring-blue-500"
                      >
                        {(() => {
                          const year = new Date().getFullYear();
                          return Array.from({ length: 21 }, (_, i) => year - 10 + i).map(y => (
                            <option key={y} value={y}>{y}</option>
                          ));
                        })()}
                      </select>
                    </div>
                    <button
                      onClick={() => setPickerValue(format(addMonths(new Date(pickerValue), 1), 'yyyy-MM-dd'))}
                      className="p-2 rounded-full hover:bg-gray-100 focus:outline-none"
                    >
                      <FiChevronRight className="w-5 h-5 text-gray-600" />
                    </button>
                  </div>

                  {/* Day-of-week header */}
                  <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-gray-500 mb-2">
                    {['Mo','Tu','We','Th','Fr','Sa','Su'].map(d => <div key={d}>{d}</div>)}
                  </div>

                  {/* Days grid */}
                  <div className="grid grid-cols-7 gap-1">
                    {eachDayOfInterval({
                      start: startOfWeek(startOfMonth(new Date(pickerValue)), { weekStartsOn: 1 }),
                      end:   endOfMonth(new Date(pickerValue)),
                    }).map(day => {
                      const iso = day.toISOString().slice(0,10);
                      const inMonth = day.getMonth() === new Date(pickerValue).getMonth();
                      return (
                        <button
                          key={iso}
                          onClick={() => {
                            setPickerValue(iso);
                            setCenterDate(new Date(iso));
                            close();
                          }}
                          className={clsx(
                            'w-8 h-8 flex items-center justify-center text-sm rounded-full transition',
                            inMonth ? 'hover:bg-blue-100' : 'text-gray-300',
                            iso === pickerValue && 'bg-blue-600 text-white'
                          )}
                        >
                          {day.getDate()}
                        </button>
                      );
                    })}
                  </div>
                </PopoverPanel>
              </Transition>
            </>
          )}
        </Popover>
        <button onClick={handleToday} className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">Today</button>
        <button onClick={handlePrevWeek} title="Previous Week" className="p-1 bg-gray-200 rounded hover:bg-gray-300"><FiChevronLeft /></button>
        <button onClick={handleNextWeek} title="Next Week" className="p-1 bg-gray-200 rounded hover:bg-gray-300"><FiChevronRight /></button>
      </div>

      {/* Weekday Labels */}
      <div className="grid grid-cols-7 gap-2 text-center text-sm font-medium text-gray-600 mb-2">
        {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(d => <div key={d} className="py-2">{d}</div>)}
      </div>

      {/* Calendar Grid */}
      <div ref={calendarRef} onScroll={scrollHandlerRef.current} className="h-[calc(100vh-200px)] overflow-auto px-4 bg-white">
        <div className="grid gap-1 divide-x divide-y divide-gray-200 border border-gray-200 grid-cols-[repeat(7,minmax(200px,1fr))]">
          {dates.map(dateObj => {
            const iso = dateObj.toISOString().slice(0,10);
            const day = trainingPlan[iso] || { planned: [], strava: null };
            const isOver = dragOverDate === iso;
            return (
              <div
                data-date={iso}
                key={iso}
                className={clsx(
                  'group relative rounded-none p-2 min-h-[250px] flex flex-col justify-between transition duration-200',
                  iso === new Date().toISOString().slice(0,10)
                    ? 'bg-yellow-100 ring-1 ring-yellow-400'
                    : 'bg-white hover:ring-1 hover:ring-blue-400',
                  isOver && 'ring-4 ring-blue-300 bg-blue-50'
                )}
                onDragOver={e => { e.preventDefault(); setDragOverDate(iso); }}
                onDragLeave={() => setDragOverDate(null)}
                onDrop={e => { e.preventDefault(); setDragOverDate(null); try { const { id, date: from } = JSON.parse(e.dataTransfer.getData('application/json')); if (from !== iso) moveWorkout(id, from, iso); } catch {} }}
              >
                <div className="text-xs text-gray-400 font-semibold mb-1">{getLabelForDate(iso)}</div>
                <div className="flex-1 flex flex-col space-y-2 overflow-y-auto">
                  {day.planned.map(w => <WorkoutCard key={w.id} workout={w} onEdit={handleEdit} />)}
                  {day.strava && <WorkoutCard workout={{ ...day.strava, date: iso, type: 'strava' }} onEdit={null} />}
                  <div onClick={() => handleAdd(iso)} className="hidden group-hover:flex items-center justify-center p-2 mb-2 bg-white shadow rounded-lg text-gray-400 hover:text-blue-500 cursor-pointer transition"><FiPlus size={20} /></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal */}
      {modalVisible && (
        <WorkoutModal
          key={`${selectedDate}-${editingWorkout?.id || 'new'}`}
          visible={modalVisible}
          date={selectedDate}
          editingWorkout={editingWorkout}
          onClose={() => setModalVisible(false)}
          onSaveSuccess={() => { setModalVisible(false); loadTrainingPlan(); }}
          containerRef={calendarRef}
        />
      )}
    </div>
  );
}
