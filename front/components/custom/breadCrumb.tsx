"use client";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { usePathname } from "next/navigation";
import React from "react";

type HeaderProps = {
  link: string;
};

function BreadCrumbElement({ link }: HeaderProps) {
  const paths = link.split("/");

  function getPathTo(segment: string) {
    const parts = usePathname().split("/").filter(Boolean);
    segment = segment.slice(2);
    const index = parts.indexOf(segment);

    if (parts.join("/") == segment) return "/" + segment;

    if (index === -1) return "/";

    return "/" + parts.slice(0, index + 1).join("/");
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
      {paths.map((seg, i) => {
        const href = "/" + paths.slice(0, i + 1).join("/");
        const url = getPathTo(href);

        if (href === "/") {
          console.log(paths);
          return (
            <React.Fragment key={i}>
              <button>
                <BreadcrumbItem>
                  <BreadcrumbLink href={url}>home</BreadcrumbLink>
                </BreadcrumbItem>
              </button>
              {i < paths.length - 1 && paths[1] !== "" && (
                <BreadcrumbSeparator />
              )}
            </React.Fragment>
          );
        }

        return (
          <React.Fragment key={i}>
            <button>
              <BreadcrumbItem>
                <BreadcrumbLink href={url}>{seg}</BreadcrumbLink>
              </BreadcrumbItem>
            </button>
            {i < paths.length - 1 && <BreadcrumbSeparator />}
          </React.Fragment>
        );
      })}
    </div>
  );
}

export default function BreadCrumb() {
  const pathName = usePathname();
  return (
    <div>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadCrumbElement link={pathName} />
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  );
}
