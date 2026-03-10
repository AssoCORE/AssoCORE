"use client"

import { AppSidebar } from "@/components/custom/sidebar"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription } from "@/components/ui/card"
import { Calendar } from "@/components/ui/calendar"
import { format } from "date-fns"
import { fr } from "date-fns/locale"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { SidebarProvider } from "@/components/ui/sidebar"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"

import { textEdit } from "@/components/custom/textEdit"

import { useState } from "react"

export default function Home() {

  const defaultUser = {
    name: "Jean",
    surname: "Dupont",
    email: "jean@email.com",
    phoneNumber: "0612345678",
    date: new Date("1995-05-10")
  }

  const [name, setName] = useState(defaultUser.name)
  const [surname, setSurname] = useState(defaultUser.surname)
  const [date, setDate] = useState<Date | undefined>(defaultUser.date)
  const [email, setEmail] = useState(defaultUser.email)
  const [phoneNumber, setPhoneNumber] = useState(defaultUser.phoneNumber)

  // Image upload
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>("/default_image.png")

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return
    const file = e.target.files[0]
    setImage(file)
    const objectUrl = URL.createObjectURL(file)
    setPreview(objectUrl)
  }

  // Regex
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  const phoneRegex = /^(?:0|\+33)[1-9](?:\d{2}){4}$/

  const [emailError, setEmailError] = useState<string | null>(null)
  const [phoneError, setPhoneError] = useState<string | null>(null)

  // Validation email
  const handleEmailChange = (value: string) => {
    setEmail(value)
    if (!emailRegex.test(value)) {
      setEmailError("Email invalide")
    } else {
      setEmailError(null)
    }
  }

  // Validation phone number
  const handlePhoneChange = (value: string) => {
    setPhoneNumber(value)
    if (!phoneRegex.test(value)) {
      setPhoneError("Numéro de téléphone invalide")
    } else {
      setPhoneError(null)
    }
  }

  return (
    <SidebarProvider>
      <div className="flex">
        <AppSidebar />
        <main
          className="p-6"
          aria-label="Page de profile"
        >
          <Card className="w-full p-6">
            <CardContent className="space-y-6 pt-6">
              <h1 className="text-2xl font-semibold">
                Page de profile
              </h1>

              <CardDescription>
                Dans cette page, vous avez accès aux informations de votre compte.
              </CardDescription>

              {/* Picture profile */}
              <div className="flex flex-col items-center gap-4">
                <Avatar className="w-24 h-24">
                  <AvatarImage
                    src={preview || "/default_image.png"}
                    alt="Photo de profil"
                  />
                  <AvatarFallback>
                    {name?.[0]}
                    {surname?.[0]}
                  </AvatarFallback>
                </Avatar>

                <Input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  aria-label="Choisir une image de profile"
                />
              </div>

              {/* Surname */}
              {textEdit("Prénom", name, setName, "Entrer son prénom")}

              {/* Name */}
              {textEdit("Nom de famille", surname, setSurname, "Entrer son nom")}

              {/* Date */}
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full justify-start"
                    aria-label="Choisir une date de naissance"
                  >
                    {date
                      ? format(date, "PPP", { locale: fr })
                      : "Choisir une date"}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={date}
                    onSelect={setDate}
                    locale={fr}
                    captionLayout="dropdown"
                    fromYear={1900}
                    toYear={new Date().getFullYear()}
                    disabled={(date) => date > new Date()}
                  />
                </PopoverContent>
              </Popover>

              {/* Email */}
              {textEdit("Adresse électronique", email, handleEmailChange, "Entrer son email")}
              {emailError && <p className="text-red-500 text-sm">{emailError}</p>}

              {/* Phone number */}
              {textEdit("Numéro de téléphone", phoneNumber, handlePhoneChange, "Entrer son numéro")}
              {phoneError && <p className="text-red-500 text-sm">{phoneError}</p>}
            </CardContent>
          </Card>
        </main>
      </div>
    </SidebarProvider>
  )
}
