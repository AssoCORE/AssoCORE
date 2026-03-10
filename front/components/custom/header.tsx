"use client";

import { usePathname } from "next/navigation";
import BreadCrumb from "@/components/custom/breadCrumb";
import DarkButton from "@/components/custom/darkButton";
import ProfileAccess from "@/components/custom/profileAccess";

type HeaderProps = {
  link: string;
};

export default function header() {
  const pathName = usePathname();

  return (
    <div className="flex items-center justify-between w-full">
      <BreadCrumb />
      <ProfileAccess />
      <DarkButton />
    </div>
  );
}
