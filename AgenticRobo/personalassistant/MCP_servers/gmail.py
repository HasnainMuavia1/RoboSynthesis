from fastmcp import FastMCP
from gmail_client import GmailService  # You will write this using Google API
from utils import parse_natural_input  # NLP logic

mcp = FastMCP("Gmail Assistant")

gmail = GmailService()  # OAuth authenticated service

@mcp.tool
def search_email(query: str) -> list:
    return gmail.search_emails(query)

@mcp.tool
def get_email_details(email_id: str) -> dict:
    return gmail.get_email(email_id)

@mcp.tool
def send_email(to: str, subject: str = "", body: str = "", cc: str = "", bcc: str = "") -> str:
    return gmail.send_email(to, subject, body, cc, bcc)

@mcp.tool
def smart_send(request: str) -> str:
    parsed = parse_natural_input(request)
    return gmail.send_email(**parsed)
