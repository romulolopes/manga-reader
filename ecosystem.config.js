module.exports = {
  apps: [
    {
      name: "manga-api",
      script: "venv/bin/gunicorn",
      args: "manga.wsgi:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 1",

      cwd: "/home/ubuntu/manga-reader",

      interpreter: "none",

      autorestart: true,
      watch: false,

      max_memory_restart: "500M",

      env: {
        PYTHONUNBUFFERED: "1"
      }
    }
  ]
};
