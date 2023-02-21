# devsummit2023-enterprise-log-archive

This code runs serverless and gathers all logs from all instances registered to your portal and archives them to AWS S3.  This is meant as a proof-of-concept/inspiration.

To run in GitHub Actions
1. Click `Use this template` -> `Create a new repository` (note, using a public repo allows you to use Actions for free as of this writing)
2. In your new repository, configure secrets for:
  - AWS: (for s3 access)
    - `AWS_ACCESS_KEY_ID`
    - `AWS_SECRET_ACCESS_KEY`
    - `AWS_S3_BUCKET` (else it will default to `devsummit-logging-archive`)
    - Ensure the bucket above is created in your account and the Access Key has write access
    - `AWS_S3_LOG_FILENAME` (else it will default to `logs-<timestamp>.json`)
  - ArcGIS:
    - `ARCGIS_PORTAL_URL` (the full url to the Portal web adaptor, e.g. `https://arcgis.myenterprise.net/portal`)
    - `ARCGIS_PORTAL_ADMIN` (Admin username with read access to logs)
    - `ARCGIS_PORTAL_ADMIN_PASSWORD` (Password for above account)
3. Run the Action from `main` to test
4. Configure cron or other triggers.  See GitHub Actions documentation.
5. 🎉
