"use client"

import { useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { loginSchema, type LoginInput } from "@/lib/auth/schemas"

// Only same-origin targets. Checking the raw string isn't enough ("//evil.com",
// "/\evil.com", or "/\t/evil.com" once the browser strips the tab), so resolve
// it the way the browser will and compare origins. The resolved path must also
// not start with "//" or "/\": "/.//evil.com" resolves same-origin to the path
// "//evil.com", which router.push() then treats as a protocol-relative URL.
function safeNext(next: string | null): string {
  if (!next) return "/"
  try {
    const url = new URL(next, window.location.origin)
    if (url.origin !== window.location.origin) return "/"
    const out = url.pathname + url.search + url.hash
    if (!out.startsWith("/") || out.startsWith("//") || out.startsWith("/\\")) {
      return "/"
    }
    return out
  } catch {
    return "/"
  }
}

export function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const form = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  })

  async function onSubmit(values: LoginInput) {
    setError(null)
    setSubmitting(true)
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      })

      if (res.ok) {
        router.push(safeNext(searchParams.get("next")))
        router.refresh()
        return
      }

      if (res.status === 401) {
        setError("Invalid username or password")
      } else if (res.status === 429) {
        setError("Too many attempts — try again in a minute")
      } else {
        setError("Service unavailable — try again shortly")
      }
    } catch {
      setError("Service unavailable — try again shortly")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Log in</CardTitle>
      </CardHeader>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Username</FormLabel>
                  <FormControl>
                    <Input autoComplete="username" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input type="password" autoComplete="current-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {error && <p className="text-destructive text-sm">{error}</p>}
          </CardContent>
          <CardFooter className="flex flex-col gap-2">
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Logging in..." : "Log in"}
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>
  )
}
