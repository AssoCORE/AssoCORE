"use client"

import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { useState } from "react"
import Link from "next/link"

import { textEdit } from "@/components/custom/textEdit"
import { Button } from "@/components/ui/button"

export default function LoginPage() {

  const [mail, setMail] = useState("")
  const [password, setPassword] = useState("")

  return (
    <div className="flex justify-center items-center min-h-screen">
      <main className="p-6 w-full max-w-md" aria-label="Page de connexion">
        <Card className="p-6">
          <CardContent className="space-y-6 pt-6">
            <h1 className="text-2xl font-semibold">Se connecter</h1>
            {textEdit("Adresse mail", mail, setMail, "Entrer son adresse mail")}
            {textEdit("Mot de passe", password, setPassword, "Entrer son mot de passe")}
          </CardContent>

          <CardFooter className= "flex flex-col gap-2">
            <Button asChild className="w-full">
              <Link href="/">Se connecter</Link>
            </Button>
            <Button asChild className="w-full">
              <Link href="/registerPage">Créer un compte</Link>
            </Button>
          </CardFooter>
        </Card>
      </main>
    </div>
  )
}
