"use client";

import { usePathname } from "next/navigation";
import React, { useState } from "react";
import BreadCrumb from "@/components/custom/breadCrumb";

type HeaderProps = {
  link: string;
};

export default function header() {
  const pathName = usePathname();
  const [results, setResults] = useState<string[]>([]);

  const handleSearch = async (query: string) => {
    const res = await fetch(`/api/search?q=${query}`);
    const data = await res.json();
    setResults(data.results);
  };

  return (
    <>
      <BreadCrumb />
    </>
  );
}
