"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { type ProfileUpdate, updateMe } from "@/lib/actions";
import { passwordSchema, phoneSchema } from "@/lib/auth/schemas";
import type { UserOut } from "@/lib/types";

// Mirrors UserUpdate in back/app/schemas/classes.py: every field optional,
// an empty password means "keep the current one".
const profileSchema = z
  .object({
    username: z.string().min(1, "Requis"),
    firstname: z.string().min(1, "Requis"),
    name: z.string().min(1, "Requis"),
    mail: z.email("Email invalide"),
    phone: phoneSchema,
    birth_date: z.string().optional().or(z.literal("")),
    password: passwordSchema.optional().or(z.literal("")),
    passwordConfirm: z.string().optional().or(z.literal("")),
  })
  .refine((v) => (v.password ?? "") === (v.passwordConfirm ?? ""), {
    path: ["passwordConfirm"],
    message: "Les mots de passe ne correspondent pas",
  });
type ProfileInput = z.infer<typeof profileSchema>;

const fields: { name: keyof ProfileInput; label: string; type?: string; auto?: string }[] = [
  { name: "username", label: "Utilisateur", auto: "username" },
  { name: "mail", label: "Email", type: "email", auto: "email" },
  { name: "firstname", label: "Prénom", auto: "given-name" },
  { name: "name", label: "Nom", auto: "family-name" },
  { name: "phone", label: "Téléphone", type: "tel", auto: "tel" },
  { name: "birth_date", label: "Date de naissance", type: "date", auto: "bday" },
  { name: "password", label: "Nouveau mot de passe", type: "password", auto: "new-password" },
  {
    name: "passwordConfirm",
    label: "Confirmer le nouveau mot de passe",
    type: "password",
    auto: "new-password",
  },
];

function defaultsOf(user: UserOut): ProfileInput {
  return {
    username: user.username,
    firstname: user.firstname,
    name: user.name,
    mail: user.mail,
    phone: user.phone ?? "",
    birth_date: user.birth_date?.slice(0, 10) ?? "",
    password: "",
    passwordConfirm: "",
  };
}

export function ProfileForm({ user }: { user: UserOut }) {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const initial = defaultsOf(user);

  const form = useForm<ProfileInput>({
    resolver: zodResolver(profileSchema),
    defaultValues: initial,
  });

  function onSubmit(values: ProfileInput) {
    // Send only what changed: the backend applies every non-null field.
    const body: ProfileUpdate = {};
    for (const key of ["username", "firstname", "name", "mail", "phone"] as const) {
      if (values[key] && values[key] !== initial[key]) body[key] = values[key];
    }
    if (values.birth_date && values.birth_date !== initial.birth_date) {
      body.birth_date = `${values.birth_date}T00:00:00`;
    }
    if (values.password) body.password = values.password;

    if (Object.keys(body).length === 0) {
      setMessage({ ok: true, text: "Aucune modification." });
      return;
    }

    setMessage(null);
    startTransition(async () => {
      const res = await updateMe(body);
      if (res.ok) {
        form.reset({ ...values, password: "", passwordConfirm: "" });
        setMessage({ ok: true, text: "Profil mis à jour." });
      } else {
        setMessage({ ok: false, text: res.error });
      }
    });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="grid gap-4 sm:grid-cols-2">
        {fields.map((f) => (
          <FormField
            key={f.name}
            control={form.control}
            name={f.name}
            render={({ field }) => (
              <FormItem>
                <FormLabel className="text-xs font-medium text-muted-foreground">
                  {f.label}
                </FormLabel>
                <FormControl>
                  <Input type={f.type} autoComplete={f.auto} {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        ))}
        <div className="flex flex-col gap-2 sm:col-span-2 sm:flex-row sm:items-center">
          <Button type="submit" className="w-full sm:w-auto" disabled={pending}>
            {pending ? "Enregistrement…" : "Enregistrer les modifications"}
          </Button>
          {message && (
            <p className={message.ok ? "text-sm text-primary" : "text-sm text-destructive"}>
              {message.text}
            </p>
          )}
        </div>
      </form>
    </Form>
  );
}
