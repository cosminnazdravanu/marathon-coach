import React, { Fragment } from "react";
import { Menu, MenuButton, MenuItem, MenuItems, Transition } from "@headlessui/react";
import { Cog6ToothIcon, ArrowRightStartOnRectangleIcon } from "@heroicons/react/24/outline";
import { useAuth } from "../auth/AuthProvider.jsx";

function initialsFrom(user){
  const s = (user?.name || user?.email || "U").trim();
  const parts = s.split(/\s+/);
  return (parts[0]?.[0] + (parts[1]?.[0] || "")).toUpperCase() || "U";
}

export default function UserMenu({ onSettings }) {
  const { user, loading, logout } = useAuth();
  const label = loading ? "…" : (user?.name || user?.email || "User");

  async function handleLogout() {
    await logout();
    window.location.href = "/";
  }

  return (
    <Menu as="div" className="relative inline-block text-left">
      <MenuButton className="flex items-center gap-2 rounded-md px-3 py-1.5 hover:bg-gray-100">
        <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 text-white text-sm font-semibold">
          {user ? initialsFrom(user) : "?"}
        </span>
        <span className="hidden sm:block max-w-[160px] truncate text-sm text-gray-700">
          {label}
        </span>
        <svg className="h-4 w-4 text-gray-500" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 1 1 1.06 1.06l-4.24 4.24a.75.75 0 0 1-1.06 0L5.21 8.29a.75.75 0 0 1 .02-1.08z"/>
        </svg>
      </MenuButton>

      <Transition
        as={Fragment}
        enter="transition duration-100"
        enterFrom="opacity-0 scale-95"
        enterTo="opacity-100 scale-100"
        leave="transition duration-75"
        leaveFrom="opacity-100 scale-100"
        leaveTo="opacity-0 scale-95"
      >
        <MenuItems className="absolute right-0 z-[9999] mt-2 w-44 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black/5 focus:outline-none">
          <div className="py-1">
            <MenuItem
              as="button"
              onClick={() => onSettings?.()}
              className="w-full px-3 py-2 text-left text-sm text-gray-700 flex items-center gap-2 data-[focus]:bg-gray-100"
            >
              <Cog6ToothIcon className="h-4 w-4" />
              Settings
            </MenuItem>

            <MenuItem
              as="button"
              onClick={handleLogout}
              className="w-full px-3 py-2 text-left text-sm text-gray-700 flex items-center gap-2 data-[focus]:bg-gray-100"
            >
              <ArrowRightStartOnRectangleIcon className="h-4 w-4" />
              Logout
            </MenuItem>
          </div>
        </MenuItems>
      </Transition>
    </Menu>
  );
}
