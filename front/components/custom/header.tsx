"use client";

import BreadCrumb from "@/components/custom/breadCrumb";
import DarkButton from "@/components/custom/darkButton";
import ProfileAccess from "@/components/custom/profileAccess";

export default function Header() {
  return (
    <header className="flex w-full items-center px-4 py-2">
      <BreadCrumb />
      <div className="ml-auto">
        <DarkButton />
        <ProfileAccess />
      </div>
    </header>
  );
}
