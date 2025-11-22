# Supabase SMTP Setup Guide

To ensure your "Forgot Password" and "Confirm Email" emails are delivered reliably, you need to configure a custom SMTP server in Supabase.

## 1. Get SMTP Credentials
You need an email delivery service. Popular options include:
- **Resend** (Recommended, generous free tier)
- **SendGrid**
- **Mailgun**
- **AWS SES**

**Example (Resend):**
1. Sign up at [resend.com](https://resend.com).
2. Create an API Key.
3. Verify your domain.

## 2. Configure Supabase
1. Go to your **Supabase Dashboard**.
2. Navigate to **Project Settings** > **Authentication** > **SMTP Settings**.
3. Toggle **Enable Custom SMTP**.
4. Enter your provider's details:
   - **Sender Email**: `noreply@yourdomain.com` (Must match verified domain)
   - **Sender Name**: `PortfolioBuilder`
   - **Host**: `smtp.resend.com` (or your provider's host)
   - **Port**: `465` (SSL) or `587` (TLS)
   - **Username**: `resend` (usually)
   - **Password**: `re_123...` (Your API Key)

## 3. Customize Email Templates
1. Go to **Authentication** > **Email Templates**.
2. **Reset Password**:
   - Subject: `Reset Your Password`
   - Body: Ensure it includes `{{ .ConfirmationURL }}`.
   - **Important**: The link should point to your app's callback URL which redirects to the reset page.
   
   *Tip: Supabase handles the token generation. Our `resetPassword` action sends the user to `/auth/callback?next=/login/reset-password`, ensuring they land on the correct page after clicking the link.*
