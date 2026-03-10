"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/app/api_url";
import Link from "next/link";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";

export default function ProfileButton() {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>("/default_user.png");

  useEffect(() => {
    fetch(`${API_BASE_URL}/user/1`, {
      headers: { Authorization: `Bearer` },
    })
      .then((response) => response.json())
      .then((data) => {
        setImage(data);
        const objectURL = URL.createObjectURL(data);
        setPreview(objectURL);
      })
      .catch((e) => console.error(e));
  }, []);

  return (
    <Link href={"/profile"}>
      <Avatar>
        <AvatarImage
          src={preview || "/default_user.png"}
          alt="photo de profile"
        />
      </Avatar>
    </Link>
  );
}
