#!/usr/bin/env python3
#
# email_agent 

import sys
import openai
import os
import subprocess
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta

class get_mail:
    def __init__(self, username, password):
        # Replace these with your own credentials
        self.username = username 
        self.password = password 

    def get_role(self):
        role = """You are an e-mail assistant. You read in a list of e-mails containing from, subject and body and converse about those messages. Your job is as follows.
1. Identify messages that may be of importance and highlight details about those messages.
2. Identify messages that may be considered spam.
3. Analyze the pattern of all the messages and look for common messages that may represent a larger message all together.
4. Provide a brief summary of the messages found.
5. Provide further analaysis upon request.
All output will be in markdown .md format. If the "check::" command is issued then only analyze the changes in the difference of the last summary and the current one you will provide. You will be intelligent on the differences between repeated summaries of message listing and only look for the differenc when "check::" is used.
"""
        return role

    # Function to decode email subject and sender
    def decode_str(self, s, encoding):
        if isinstance(s, bytes):
            return s.decode(encoding if encoding else "utf-8")
        return s

    # Function to extract the body from the email message
    def get_body(self, msg):
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        return part.get_payload(decode=True).decode()
                    elif content_type == "text/html":
                        return part.get_payload(decode=True).decode()
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain" or content_type == "text/html":
                return msg.get_payload(decode=True).decode()

    def list_recent_emails(self, imap_server='imap.gmail.com', imap_port=993):
        # Connect to the server
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)

        # Login to your account
        mail.login(self.username, self.password)

        # Select the mailbox you want to check (in this case, the inbox)
        mail.select("inbox", readonly=True)

        # Calculate the date for 2 days ago
        date_2_days_ago = (datetime.now() - timedelta(3)).strftime("%d-%b-%Y")
        
        # Search for emails since 2 days ago
        status, messages = mail.search(None, f'SINCE {date_2_days_ago}')

        # Convert messages to a list of email IDs
        email_ids = messages[0].split()

        # Fetch and print email details
        email_messages = ""
        for email_id in email_ids:
            # Fetch the email by ID
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    # Decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    subject = self.decode_str(subject, encoding)
                    
                    # Decode the sender's email address
                    from_ = msg.get("From")
                    
                    # Get the body of the email
                    body = self.get_body(msg)
                    
                    email_messages += f"Subject: {subject}"
                    email_messages += f"From: {from_}"
                    email_messages += f"Body:\n{body}"

        # Logout and close the connection
        mail.logout()
        return email_messages

if __name__ == "__main__":
    # Call the function to list recent emails
    getemail = get_mail()
    messages = getemail.list_recent_emails()
    print(messages)
