# **send2pbsync**

**send2pbsync** is a bridge between **Calibre-Web-Automated (CWA)** and **PBSync**, ensuring seamless delivery of eBooks from CWA to your PocketBook by reformatting email attachments for compatibility. 📚📧🚀

---

## **What It Does**

This tool automates the process of:
1. Downloading `.epub` attachments from emails sent by Calibre-Web-Automated (CWA).
2. Repackaging them into a correctly formatted ZIP archive.
3. Sending the archive to PBSync, enabling you to read your eBooks on a PocketBook device.

---

## **Features**

- Automatically fetches emails with eBooks sent by CWA.
- Reformats attachments to ensure compatibility with PBSync.
- Sends the corrected archive to PBSync via email.
- Runs periodically using a scheduler for hands-free operation.

---

## **Prerequisites**

Before setting up **send2pbsync**, ensure you have:
- Access to an IMAP and SMTP email account (e.g., Gmail).
- Docker installed on your system.
- Basic knowledge of environment variables.

---

## **Quick Start**

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/send2pbsync.git
cd send2pbsync
```

### 2. Configure Environment Variables
Edit the `docker-compose.yaml` file and replace the placeholder values in the `environment` section with your actual email credentials and settings:

```yaml
environment:
  - IMAP_SERVER=imap.gmail.com
  - IMAP_USER=your-email@gmail.com
  - IMAP_PASSWORD=your-imap-password
  - SMTP_SERVER=smtp.gmail.com
  - SMTP_PORT=587
  - SMTP_USER=your-email@gmail.com
  - SMTP_PASSWORD=your-smtp-password
  - SEND_TO_EMAIL=your-pocketbook-email@example.com
  - SMTP_USE_TLS=True
  - SMTP_FROM_EMAIL=your-email@gmail.com
```

### 3. Run the Service
Start the application using Docker Compose:
```bash
docker-compose up -d
```

### 4. Verify the Setup
Check the logs to ensure everything is running smoothly:
```bash
docker logs scheduler
```

---

## **How It Works**

1. The **scheduler** runs the **send2pbsync** service every 10 minutes (configurable).
2. The service connects to your IMAP server, downloads `.epub` attachments from emails sent by CWA, and deletes the processed emails.
3. It creates a ZIP archive of the downloaded `.epub` files.
4. The ZIP file is sent to your PBSync email address, making it available on your PocketBook device.

---

## **Customization**

- **Change the Schedule**: Modify the `ofelia.job-run.send2pbsync.schedule` label in `docker-compose.yaml` to adjust how often the service runs (e.g., `@every 5m` for every 5 minutes).
- **Use a Different Email Provider**: Update the `IMAP_SERVER`, `SMTP_SERVER`, and related variables to match your email provider's settings.

---

## **Contributing**

We welcome contributions! If you'd like to improve **send2pbsync**, feel free to fork the repository, make your changes, and submit a pull request.

---

## **License**

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## **Support**

If you encounter any issues or have questions, feel free to open an issue in the repository.

Happy reading! 📚✨
