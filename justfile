set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# Fleet minimal justfile (mcp_fleet_lint_apply)

# Open the interactive recipe dashboard in the browser
default:
    @just --list

lint:
	Set-Location '{{justfile_directory()}}'
	uv run ruff check .

fix:
	Set-Location '{{justfile_directory()}}'
	uv run ruff check . --fix
	uv run ruff format .
