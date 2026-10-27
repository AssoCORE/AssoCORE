"use client";

import { SlidersHorizontal } from "lucide-react";
import { format } from "date-fns";
import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/custom/data-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  budgetTotals,
  historyRequests,
  pendingRequests,
  type BudgetCategory,
} from "@/lib/mock/budget";
import { formatEuros } from "@/lib/format";
import type { BudgetRequest } from "@/lib/types";

const columns: DataTableColumn<BudgetRequest>[] = [
  {
    key: "date",
    header: "Date",
    render: (r) => (
      <span className="tabular-nums text-muted-foreground">
        {format(r.date, "dd/MM/yyyy")}
      </span>
    ),
    className: "w-28",
    headerClassName: "w-28",
  },
  {
    key: "name",
    header: "Nom de la demande",
    render: (r) => <span className="font-medium">{r.name}</span>,
  },
  {
    key: "reason",
    header: "Motif",
    render: (r) => <span className="text-muted-foreground">{r.reason}</span>,
    className: "w-32",
    headerClassName: "w-32",
  },
  {
    key: "amount",
    header: "Montant",
    render: (r) => <span className="tabular-nums font-semibold">{formatEuros(r.amountEur)}</span>,
    className: "w-28 text-right",
    headerClassName: "w-28 text-right",
  },
];

export default function BudgetPage() {
  const [category, setCategory] = useState<BudgetCategory>("Total");
  const amount = budgetTotals[category];

  const pending = useMemo(() => pendingRequests, []);
  const history = useMemo(() => historyRequests, []);

  return (
    <div className="flex flex-1 flex-col gap-4 md:gap-6">
      <Card>
        <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between md:p-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-lg font-semibold">Budget</span>
            <Select value={category} onValueChange={(v) => setCategory(v as BudgetCategory)}>
              <SelectTrigger className="min-w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.keys(budgetTotals).map((k) => (
                  <SelectItem key={k} value={k}>
                    {k}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span className="text-lg font-semibold tabular-nums">:</span>
            <span className="text-2xl font-bold tabular-nums">{formatEuros(amount)}</span>
          </div>
          <Button>Faire une demande</Button>
        </CardContent>
      </Card>

      <div className="grid flex-1 min-h-0 auto-rows-fr gap-4 md:gap-6 lg:grid-cols-2">
        <BudgetTable title="Demande en attente :" data={pending} />
        <BudgetTable
          title="Historique :"
          data={history}
          action={
            <Button size="sm" className="gap-1">
              <SlidersHorizontal className="size-3.5" />
              Filtres
            </Button>
          }
        />
      </div>
    </div>
  );
}

function BudgetTable({
  title,
  data,
  action,
}: {
  title: string;
  data: BudgetRequest[];
  action?: React.ReactNode;
}) {
  return (
    <Card className="h-full min-h-0">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
        {action}
      </CardHeader>
      <CardContent className="flex flex-1 flex-col overflow-hidden p-0">
        <div className="flex-1 overflow-y-auto">
          <DataTable columns={columns} data={data} rowKey={(r) => r.id} />
        </div>
      </CardContent>
    </Card>
  );
}
