import React from "react"
import { Input } from "@/components/ui/input"

export function textEdit(
  label: string,
  value: string,
  setter: React.Dispatch<React.SetStateAction<string>>,
  ariaLabel: string
) {
  return (
    <Input
      placeholder={label}
      value={value}
      onChange={(e) => setter(e.target.value)}
      aria-label={ariaLabel}
    />
  )
}
