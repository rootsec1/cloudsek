# cloudsek
### Design
I am using Firebase RealTime DB as I feel it best suits the needs. (Persistence + RealTime)
Upon receiving a URL or a file (via /upload), a unique UUID is generated.
There exists a global hashtable that takes in the above UUID as key and stores metadata about that file's current download progress as it's value (another JSON).

Example of <Key:Value> (UUID: Another JSON)
0c2fdbdb8b584a4aaad7030524b72bb2: {
    done: 13658590
    name: "backeend_chalenge.pdf"
    remaining: 0
    size: 13658590
    status: "completed"
}

Therefore every file upload/download instance has a separate UUID. In simple language, multiple download or upload instances of even the same file will leverage different UUIDs and therefore file to DB mapping is consistent.

### Working
1. Download via file URL
2. Ability to check status of download
3. Option to download a file
4. Option to upload a file
5. Ability to terminate a download (Was not able to get pause/resume functionality to work)
6. Rate limiting (Defaults to 10 requests per 1 minute)

### Not Working
1. Pause and Resume download functionality
2. Estimated time of file download completion
3. Frontend to leverage the built APIs

