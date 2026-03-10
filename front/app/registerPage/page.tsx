"use client"

import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { useState } from "react"
import Link from "next/link"

import { textEdit } from "@/components/custom/textEdit"
import { Button } from "@/components/ui/button"

export default function LoginPage() {

  const [name, setName] = useState("")
  const [surname, setSurname] = useState("")
  const [mail, setMail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const [errors, setErrors] = useState({
    name: "",
    surname: "",
    mail: "",
    password: "",
    confirmPassword: ""
  })

  // Regex
  const nameRegex = /^[A-Za-zÀ-ÖØ-öø-ÿ'-]{2,30}$/
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,}$/

  // Validation handlers
  const handleNameChange = (value: string) => {
    setName(value)
    setErrors(prev => ({
      ...prev,
      name: nameRegex.test(value) ? "" : "Prénom invalide"
    }))
  }

  const handleSurnameChange = (value: string) => {
    setSurname(value)
    setErrors(prev => ({
      ...prev,
      surname: nameRegex.test(value) ? "" : "Nom invalide"
    }))
  }

  const handleMailChange = (value: string) => {
    setMail(value)
    setErrors(prev => ({
      ...prev,
      mail: emailRegex.test(value) ? "" : "Email invalide"
    }))
  }

  const handlePasswordChange = (value: string) => {
    setPassword(value)
    setErrors(prev => ({
      ...prev,
      password: passwordRegex.test(value)
        ? ""
        : "8 caractères minimum avec au moins 1 chiffre, 1 majuscule et un caractère spécial"
    }))
  }

  const handleConfirmPasswordChange = (value: string) => {
    setConfirmPassword(value)
    setErrors(prev => ({
      ...prev,
      confirmPassword: value === password ? "" : "Les mots de passe ne correspondent pas"
    }))
  }

  return (
    <div className="flex justify-center items-center min-h-screen">
      <main className="p-6 w-full max-w-md" aria-label="Page de login">
        <Card className="p-6">

          <CardContent className="space-y-6 pt-6">

            <h1 className="text-2xl font-semibold">Créer un compte</h1>

            {textEdit("Prénom", name, handleNameChange, "Entrer son prénom")}
            {errors.name && <p className="text-red-500 text-sm">{errors.name}</p>}

            {textEdit("Nom de famille", surname, handleSurnameChange, "Entrer son nom")}
            {errors.surname && <p className="text-red-500 text-sm">{errors.surname}</p>}

            {textEdit("Adresse mail", mail, handleMailChange, "Entrer son email")}
            {errors.mail && <p className="text-red-500 text-sm">{errors.mail}</p>}

            {textEdit("Mot de passe", password, handlePasswordChange, "Entrer son mot de passe")}
            {errors.password && <p className="text-red-500 text-sm">{errors.password}</p>}

            {textEdit("Confirmer le mot de passe", confirmPassword, handleConfirmPasswordChange, "Confirmer le mot de passe")}
            {errors.confirmPassword && <p className="text-red-500 text-sm">{errors.confirmPassword}</p>}

          </CardContent>

          <CardFooter className="flex flex-col gap-2">

            <Button asChild variant="outline" className="w-full">
              <Link href="/loginPage">Créer son compte</Link>
            </Button>

            <Button asChild variant="outline" className="w-full">
              <Link href="/loginPage">Se connecter</Link>
            </Button>

          </CardFooter>

        </Card>
      </main>
    </div>
  )
}
