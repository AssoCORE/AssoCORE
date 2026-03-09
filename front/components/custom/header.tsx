"use client";

import { usePathname } from "next/navigation";
import BreadCrumb from "@/components/custom/breadCrumb";
import DarkButton from "./darkButton";

type HeaderProps = {
  link: string;
};

export default function header() {
  const pathName = usePathname();

  return (
    <div className="flex items-center justify-between w-full">
      <BreadCrumb />
      <DarkButton />
    </div>
  );
}
