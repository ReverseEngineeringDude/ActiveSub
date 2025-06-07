import asyncio
import httpx
from rich.console import Console
from rich.progress import Progress

console = Console()

# Load subdomains
with open("./subdomain/subdom.txt", "r") as file:
    subdomains = file.read().splitlines()

# Output files
file_200 = open("./200.txt", "a")
file_404 = open("./404.txt", "a")

async def check_subdomain(subdomain, client):
    url = f"https://{subdomain}/"
    try:
        response = await client.get(url, timeout=5)

        if response.status_code == 200:
            console.print(f"[green][+] Active:[/] {subdomain}")
            file_200.write(subdomain + "\n")

        elif response.status_code == 404:
            console.print(f"[yellow][404 Not Found]:[/] {subdomain}")
            file_404.write(subdomain + "\n")

        else:
            console.print(f"[cyan][{response.status_code}]:[/] {subdomain}")

    except httpx.RequestError:
        console.print(f"[red][-] Failed:[/] {subdomain}")

async def main():
    tasks = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        with Progress() as progress:
            task = progress.add_task("[blue]Checking subdomains...", total=len(subdomains))
            for sub in subdomains:
                tasks.append(check_subdomain(sub.strip(), client))
                progress.update(task, advance=1)
            await asyncio.gather(*tasks)

    file_200.close()
    file_404.close()
    console.print("\n[bold green]✓ Done! Check 200.txt and 404.txt[/]")

# Run it
try:
    asyncio.run(main())
except KeyboardInterrupt:
    console.print("\n[bold red]❌ User stopped the scan.")
