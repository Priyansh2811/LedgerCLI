#!/usr/bin/env python3
"""
LedgerCLI - High Performance Terminal Expense Tracker
Features:
- Local SQLite database (~/.ledgercli.db)
- Natural language quick-add string parser
- Category budget limits & real-time overspending alerts
- Rich formatted tables and analytics summaries
- CSV transaction export
"""
import os
import sys
import sqlite3
import argparse
import datetime
import re
import csv
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

DB_PATH = Path.home() / ".ledgercli.db"
console = Console()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        payment_mode TEXT DEFAULT 'Cash',
        created_at DATE NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        category TEXT PRIMARY KEY,
        monthly_limit REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_expense(amount: float, category: str, desc: str, mode: str = "Cash", date_str: str = None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    date_val = date_str if date_str else datetime.date.today().isoformat()
    cur.execute(
        "INSERT INTO expenses (amount, category, description, payment_mode, created_at) VALUES (?, ?, ?, ?, ?)",
        (amount, category.title(), desc, mode, date_val)
    )
    conn.commit()

    # Check budget thresholds
    cur.execute("SELECT monthly_limit FROM budgets WHERE category = ?", (category.title(),))
    row = cur.fetchone()
    warning = ""
    if row:
        limit = row[0]
        cur.execute(
            "SELECT SUM(amount) FROM expenses WHERE category = ? AND strftime('%Y-%m', created_at) = strftime('%Y-%m', ?)",
            (category.title(), date_val)
        )
        total_spent = cur.fetchone()[0] or 0.0
        if total_spent > limit:
            warning = f"\n[bold red]⚠ OVER BUDGET ALERT:[/bold red] Spent ₹{total_spent:.2f} of ₹{limit:.2f} monthly limit for {category.title()}!"
        elif total_spent >= limit * 0.8:
            warning = f"\n[bold yellow]⚠ CAUTION:[/bold yellow] Reached {int((total_spent/limit)*100)}% of monthly budget for {category.title()}."

    conn.close()
    console.print(f"[bold green]✔ Logged successfully:[/bold green] ₹{amount:.2f} under [cyan]{category.title()}[/cyan] ({desc or 'No description'}) via {mode}.{warning}")

def quick_add(text: str):
    """Parses strings like: '450 for coffee via upi' or '1200 groceries card'"""
    amount_match = re.search(r"(\d+(\.\d+)?)", text)
    if not amount_match:
        console.print("[red]Could not parse amount from your input.[/red]")
        return
    amount = float(amount_match.group(1))
    clean = text.replace(amount_match.group(1), "").strip()

    mode = "Cash"
    if re.search(r"\b(upi|gpay|paytm|phonepe)\b", clean, re.I):
        mode = "UPI"
        clean = re.sub(r"\b(via\s+)?(upi|gpay|paytm|phonepe)\b", "", clean, flags=re.I)
    elif re.search(r"\b(card|credit|debit)\b", clean, re.I):
        mode = "Card"
        clean = re.sub(r"\b(via\s+)?(card|credit|debit)\b", "", clean, flags=re.I)

    parts = re.split(r"\bfor\b", clean, flags=re.I)
    desc = parts[-1].strip() if len(parts) > 1 else clean.strip()
    category = desc.split()[0].title() if desc else "General"
    add_expense(amount, category, desc, mode)

def list_expenses(limit: int = 15, category: str = None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if category:
        cur.execute(
            "SELECT id, amount, category, description, payment_mode, created_at FROM expenses WHERE category = ? ORDER BY created_at DESC, id DESC LIMIT ?",
            (category.title(), limit)
        )
    else:
        cur.execute(
            "SELECT id, amount, category, description, payment_mode, created_at FROM expenses ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,)
        )
    rows = cur.fetchall()
    conn.close()

    table = Table(title=f"Recent Transactions (Last {limit})", show_lines=True)
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Date", justify="center")
    table.add_column("Category", style="cyan")
    table.add_column("Description")
    table.add_column("Mode", justify="center")
    table.add_column("Amount", justify="right", style="bold green")

    total = 0.0
    for r in rows:
        total += r[1]
        table.add_row(str(r[0]), str(r[5]), r[2], r[3] or "-", r[4], f"₹{r[1]:.2f}")

    console.print(table)
    console.print(f"[bold]Total for displayed records:[/bold] [green]₹{total:.2f}[/green]\n")

def set_budget(category: str, limit: float):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO budgets (category, monthly_limit) VALUES (?, ?)", (category.title(), limit))
    conn.commit()
    conn.close()
    console.print(f"[bold green]✔ Budget saved:[/bold green] ₹{limit:.2f}/month for [cyan]{category.title()}[/cyan]")

def export_csv(filepath: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, amount, category, description, payment_mode, created_at FROM expenses ORDER BY created_at ASC")
    rows = cur.fetchall()
    conn.close()

    path = Path(filepath).expanduser()
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Amount", "Category", "Description", "Payment Mode", "Date"])
        writer.writerows(rows)
    console.print(f"[bold green]✔ Exported {len(rows)} records to[/bold green] [cyan]{path}[/cyan]")

def main():
    parser = argparse.ArgumentParser(description="LedgerCLI - Lightning fast terminal expense tracking")
    sub = parser.add_subparsers(dest="command")

    # add
    p_add = sub.add_parser("add", help="Add an expense manually")
    p_add.add_argument("-a", "--amount", type=float, required=True, help="Amount spent")
    p_add.add_argument("-c", "--category", required=True, help="Category name")
    p_add.add_argument("-d", "--desc", default="", help="Description")
    p_add.add_argument("-m", "--mode", default="Cash", help="Payment mode (Cash, UPI, Card)")
    p_add.add_argument("--date", default=None, help="Date in YYYY-MM-DD format")

    # quick
    p_quick = sub.add_parser("quick", help="Quick add using natural language")
    p_quick.add_argument("text", nargs="+", help="Example: 450 for team lunch via upi")

    # list
    p_list = sub.add_parser("list", help="List recent expenses")
    p_list.add_argument("-n", "--limit", type=int, default=15, help="Number of records to show")
    p_list.add_argument("-c", "--category", default=None, help="Filter by category")

    # budget
    p_budget = sub.add_parser("budget", help="Manage budget limits")
    b_sub = p_budget.add_subparsers(dest="budget_action")
    p_b_set = b_sub.add_parser("set", help="Set monthly category budget")
    p_b_set.add_argument("-c", "--category", required=True, help="Category name")
    p_b_set.add_argument("-l", "--limit", type=float, required=True, help="Monthly limit in currency")

    # export
    p_export = sub.add_parser("export", help="Export transactions to CSV")
    p_export.add_argument("-o", "--output", default="expenses.csv", help="Target CSV file path")

    args = parser.parse_args()

    if args.command == "add":
        add_expense(args.amount, args.category, args.desc, args.mode, args.date)
    elif args.command == "quick":
        quick_add(" ".join(args.text))
    elif args.command == "list":
        list_expenses(args.limit, args.category)
    elif args.command == "budget" and args.budget_action == "set":
        set_budget(args.category, args.limit)
    elif args.command == "export":
        export_csv(args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
