import { z } from "zod"

// Mirrors back/app/schemas/classes.py exactly, so client-side errors match
// the backend's 422s instead of contradicting them.
export const passwordSchema = z
  .string()
  .min(8, "Must be at least 8 characters")
  .max(50, "Must be at most 50 characters")
  .regex(
    /^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$/,
    "Must contain an uppercase letter, a lowercase letter, a digit, and one of #?!@$%^&*-"
  )

export const phoneSchema = z
  .string()
  .regex(/^\+?[1-9]\d{1,14}$/, "Invalid phone number")
  .optional()
  .or(z.literal(""))

export const loginSchema = z.object({
  username: z.string().min(1, "Required"),
  password: z.string().min(1, "Required"),
})
export type LoginInput = z.infer<typeof loginSchema>

export const registerSchema = z.object({
  name: z.string().min(1, "Required"),
  firstname: z.string().min(1, "Required"),
  username: z.string().min(1, "Required"),
  password: passwordSchema,
  mail: z.email("Invalid email"),
  phone: phoneSchema,
  birth_date: z.string().optional().or(z.literal("")),
})
export type RegisterInput = z.infer<typeof registerSchema>
