"use client";

import {
  Button as MuiButton,
  Card,
  CardContent,
  Typography,
} from "@mui/material";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 p-8">
      <main className="flex flex-col gap-8 max-w-4xl w-full">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-2">AssoCORE</h1>
          <p className="text-zinc-600">Association Management Platform</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Material-UI
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                className="mb-4"
              >
                Component library with Material Design
              </Typography>
              <MuiButton variant="contained" color="primary">
                MUI Button
              </MuiButton>
            </CardContent>
          </Card>

          <div className="border rounded-lg p-6 bg-white">
            <h2 className="text-xl font-semibold mb-2">shadcn/ui + Tailwind</h2>
            <p className="text-sm text-zinc-600 mb-4">
              Customizable components built with Radix UI
            </p>
            <button className="px-4 py-2 bg-zinc-900 text-white rounded-md hover:bg-zinc-800">
              Tailwind Button
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
